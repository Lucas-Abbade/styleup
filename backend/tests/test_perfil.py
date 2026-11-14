"""Perfil, consentimento e exclusão de conta (fase 1, itens 4 e 5)."""

from __future__ import annotations

from app.config import config
from app.repositorio.memoria import armazem

from .conftest import cabecalho, nova_peca


def test_consentimento_registra_versao_data_e_finalidades(cliente):
    h = cabecalho("nova")
    antes = cliente.get("/perfil", headers=h).json()["consentimento"]
    assert antes["aceito"] is False and antes["versao_vigente"] == config.versao_termo

    termo = cliente.get("/perfil/termo").json()
    assert termo["versao"] == config.versao_termo and termo["secoes"]
    assert [f["chave"] for f in termo["finalidades"] if f["obrigatoria"]] == ["essencial"]

    r = cliente.post("/perfil/consentimento", headers=h,
                     json={"versao": termo["versao"], "localizacao": True})
    assert r.status_code == 201
    depois = r.json()
    assert depois["aceito"] and depois["aceito_em"] and depois["localizacao"] is True
    registro = armazem.consentimentos[-1]
    assert registro["versao"] == termo["versao"]
    assert registro["finalidades"] == {"essencial": True, "localizacao": True}
    assert cliente.get("/pecas", headers=h).status_code == 200


def test_aceite_de_versao_antiga_nao_vale(cliente):
    r = cliente.post("/perfil/consentimento", headers=cabecalho("nova"),
                     json={"versao": "2020-01-v0"})
    assert r.status_code == 409 and r.json()["codigo"] == "termo_desatualizado"
    assert r.json()["versao"] == config.versao_termo


def test_revogar_fecha_as_rotas_de_dados_na_hora(cliente, ana):
    assert cliente.get("/pecas", headers=ana).status_code == 200
    assert cliente.delete("/perfil/consentimento", headers=ana).json()["aceito"] is False
    assert cliente.get("/pecas", headers=ana).json()["codigo"] == "consentimento_pendente"
    assert armazem.consentimentos[-1]["revogado_em"]          # o registro fica, carimbado
    assert cliente.get("/perfil", headers=ana).status_code == 200   # perfil segue acessível


def test_atualizar_nome(cliente, ana):
    r = cliente.put("/perfil", headers=ana, json={"nome": "  Ana   Lima "})
    assert r.json()["nome"] == "Ana Lima"
    assert cliente.put("/perfil", headers=ana, json={"nome": "   "}).status_code == 422


def test_exportar_devolve_os_dados_do_titular(cliente, ana, bruno):
    cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"})
    dados = cliente.get("/perfil/exportar", headers=ana).json()
    assert dados["pecas"] and dados["looks"] and dados["consentimentos"]
    uid = dados["perfil"]["id"]
    assert all(p["usuario_id"] == uid for p in dados["pecas"])


def test_excluir_conta_apaga_banco_e_fotos_e_poupa_os_outros(cliente, ana, bruno):
    foto = cliente.post("/demo/fotos", headers=ana,
                        files={"foto": ("p.webp", b"x", "image/webp")}).json()["caminho"]
    cliente.post("/pecas", headers=ana, json=nova_peca(imagem_path=foto))
    look = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"][0]
    cliente.post("/feedback", headers=ana, json={"look_id": look["id"], "aprovado": True})
    uid = cliente.get("/perfil", headers=ana).json()["id"]
    pecas_do_bruno = len(cliente.get("/pecas", headers=bruno).json())

    r = cliente.request("DELETE", "/perfil", headers=ana, json={"confirmacao": "sim"})
    assert r.status_code == 422 and r.json()["codigo"] == "confirmacao_invalida"
    assert uid in armazem.perfis

    r = cliente.request("DELETE", "/perfil", headers=ana, json={"confirmacao": "excluir"})
    assert r.status_code == 200 and r.json()["excluida"] and r.json()["fotos_removidas"] == 1
    assert foto not in armazem.fotos
    restos = [x for tabela in (armazem.pecas, armazem.contextos, armazem.looks)
              for x in tabela.values() if x["usuario_id"] == uid]
    assert restos == [] and uid not in armazem.perfis and uid not in armazem.preferencias
    assert not [c for c in armazem.consentimentos if c["usuario_id"] == uid]
    assert not [k for k in armazem.feedback if k[0] == uid]
    assert len(cliente.get("/pecas", headers=bruno).json()) == pecas_do_bruno
