"""Rotas de recomendação, feedback e métricas."""

from __future__ import annotations

import pytest

from app.repositorio.memoria import armazem
from app.services import clima

from .conftest import aceitar, nova_peca


def _minimo(cliente, h):
    for categoria, cor in (("camiseta", "branco"), ("calca-jeans", "azul"), ("tenis", "preto")):
        assert cliente.post("/pecas", headers=h, json=nova_peca(categoria, cor)).status_code == 201


def test_recomenda_tres_looks_completos(cliente, ana):
    r = cliente.post("/recomendacoes", headers=ana, json={"evento": "trabalho", "temperatura": 24})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert len(corpo["looks"]) == 3
    for look in corpo["looks"]:
        papeis = [p["papel"] for p in look["pecas"]]
        assert {"superior", "inferior", "calcado"} <= set(papeis)
        assert 0 <= look["score"] <= 1 and set(look["parcelas"]) == {
            "ocasiao", "clima", "cor", "estilo", "variedade"}
        assert look["titulo"] and look["resumo"] and look["explicacao"]
    assert corpo["contexto"]["evento"] == "trabalho" and not corpo["contexto"]["clima_automatico"]
    # compatibilidade: o corpo antigo ({"evento": ...}) continua aceito
    assert cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).status_code == 200


def test_guarda_roupa_vazio_nao_deixa_contexto_orfao(cliente, vazio):
    """Fase 2, item 5: o contexto era gravado antes das validações; o 409 deixava
    uma linha em `contextos` que inflava `consultas` e derrubava o Hit Rate@3."""
    r = cliente.post("/recomendacoes", headers=vazio, json={"evento": "casual"})
    assert r.status_code == 409 and r.json()["codigo"] == "guarda_roupa_vazio"

    cliente.post("/pecas", headers=vazio, json=nova_peca("camiseta", "preto"))
    r = cliente.post("/recomendacoes", headers=vazio, json={"evento": "casual"})
    assert r.status_code == 409 and r.json()["codigo"] == "sem_combinacao"
    assert set(r.json()["faltando"]) == {"inferior", "calcado"}

    assert armazem.contextos == {} and armazem.looks == {}
    assert cliente.get("/metricas", headers=vazio).json()["consultas"] == 0


def test_falha_ao_gravar_looks_nao_deixa_nada_pela_metade(cliente, ana):
    armazem.falhar_ao_gravar_looks = True
    try:
        from fastapi.testclient import TestClient
        r = TestClient(cliente.app, raise_server_exceptions=False).post(
            "/recomendacoes", headers=ana, json={"evento": "casual"})
    finally:
        armazem.falhar_ao_gravar_looks = False
    assert r.status_code == 500
    assert armazem.contextos == {} and armazem.looks == {}


def test_peca_malformada_nao_derruba_a_recomendacao(cliente, vazio):
    """Fase 2, item 8: uma linha ruim no banco quebrava todas as recomendações."""
    _minimo(cliente, vazio)
    for defeito in ({"cor_hsv": [1, 2], "cor_hex": "xx"}, {"formalidade": None},
                    {"papel": "chapeu"}, {"cor_hsv": "azul", "cor_hex": None}):
        ruim = cliente.post("/pecas", headers=vazio, json=nova_peca("polo", "marinho")).json()
        armazem.pecas[ruim["id"]].update(defeito)
    r = cliente.post("/recomendacoes", headers=vazio, json={"evento": "casual", "temperatura": 25})
    assert r.status_code == 200, r.text
    assert all(p["categoria"] != "polo" for l in r.json()["looks"] for p in l["pecas"])


def test_texto_livre_e_interpretado_e_devolvido(cliente, ana):
    r = cliente.post("/recomendacoes", headers=ana,
                     json={"texto": "Look para a faculdade, minimalista, 20 graus"})
    contexto = r.json()["contexto"]
    assert contexto["evento"] == "faculdade" and contexto["estilo"] == "minimalista"
    assert contexto["temperatura"] == 20
    assert contexto["entendido"] == ["Faculdade", "Minimalista", "20 °C"]


def test_inspiracoes_viram_contexto(cliente, ana):
    chaves = [i["chave"] for i in cliente.get("/inspiracoes").json()]
    assert chaves == ["trabalho-faculdade", "role-balada", "dias-frios", "verao",
                      "minimalista", "esportivo"]
    frio = cliente.post("/recomendacoes", headers=ana, json={"inspiracao": "dias-frios"}).json()
    assert frio["contexto"]["temperatura"] == 12
    assert all(any(p["papel"] == "sobreposicao" for p in l["pecas"]) for l in frio["looks"])

    esporte = cliente.post("/recomendacoes", headers=ana, json={"inspiracao": "esportivo"}).json()
    assert esporte["contexto"]["evento"] == "academia"
    categorias = {p["categoria"] for l in esporte["looks"] for p in l["pecas"]}
    assert not categorias & {"chinelo", "calca-jeans", "cinto", "bota"}

    assert cliente.post("/recomendacoes", headers=ana,
                        json={"inspiracao": "nao-existe"}).status_code == 400
    assert cliente.post("/recomendacoes", headers=ana,
                        json={"evento": "lua"}).json()["codigo"] == "evento_desconhecido"


def test_temperatura_informada_vence_a_inspiracao(cliente, ana):
    r = cliente.post("/recomendacoes", headers=ana,
                     json={"inspiracao": "dias-frios", "temperatura": 30}).json()
    assert r["contexto"]["temperatura"] == 30


def test_estilo_impossivel_gera_aviso_e_nao_mente_no_titulo(cliente, vazio):
    _minimo(cliente, vazio)                      # nada preto além do tênis
    r = cliente.post("/recomendacoes", headers=vazio,
                     json={"estilo": "all-black", "temperatura": 25}).json()
    assert any("all black" in a for a in r["avisos"])
    assert "All black" not in r["looks"][0]["titulo"]


def test_calor_de_cuiaba_nao_zera_a_recomendacao_de_trabalho(cliente, vazio):
    """Com o teto antigo das calças (32 °C), 38 °C + trabalho dava 409."""
    for categoria, cor in (("polo", "marinho"), ("calca-sarja", "cáqui"),
                           ("tenis-casual", "branco"), ("bermuda", "bege")):
        cliente.post("/pecas", headers=vazio, json=nova_peca(categoria, cor))
    r = cliente.post("/recomendacoes", headers=vazio, json={"evento": "trabalho", "temperatura": 38})
    assert r.status_code == 200, r.text
    assert r.json()["looks"][0]["pecas"][1]["categoria"] == "calca-sarja"


# ------------------------------------------------------------------ clima
@pytest.fixture
def clima_falso(monkeypatch):
    chamadas = []

    def previsao(lat, lon, **_):
        chamadas.append((lat, lon))
        return {"temperatura": 33.0, "sensacao": 36.0, "chuva_prob": 0.7}
    monkeypatch.setattr(clima, "previsao", previsao)
    return chamadas


def test_clima_automatico_exige_consentimento_de_localizacao(cliente, clima_falso):
    sem = aceitar(cliente, "sem-local", localizacao=False)
    r = cliente.post("/recomendacoes", headers=sem,
                     json={"evento": "casual", "latitude": -15.6, "longitude": -56.1}).json()
    assert r["contexto"]["clima_automatico"] is False and clima_falso == []

    com = aceitar(cliente, "com-local", localizacao=True)
    r = cliente.post("/recomendacoes", headers=com,
                     json={"evento": "casual", "latitude": -15.6, "longitude": -56.1}).json()
    assert r["contexto"]["clima_automatico"] is True
    assert r["contexto"]["temperatura"] == 33 and r["contexto"]["chuva_prob"] == 0.7
    assert clima_falso == [(-15.6, -56.1)]


def test_coordenadas_nunca_sao_gravadas(cliente, clima_falso):
    """Fase 1, item 4 (LGPD): a posição serve só para consultar o clima."""
    com = aceitar(cliente, "com-local", localizacao=True)
    cliente.post("/recomendacoes", headers=com,
                 json={"evento": "casual", "latitude": -15.6012, "longitude": -56.0974})
    gravado = repr(list(armazem.contextos.values())) + repr(list(armazem.looks.values()))
    assert "latitude" not in gravado and "15.6" not in gravado and "56.09" not in gravado
    assert "latitude" not in repr(cliente.get("/perfil/exportar", headers=com).json())


def test_api_de_clima_fora_do_ar_nao_derruba_a_recomendacao(cliente, monkeypatch):
    monkeypatch.setattr(clima, "previsao", lambda *a, **k: None)
    com = aceitar(cliente, "com-local", localizacao=True)
    r = cliente.post("/recomendacoes", headers=com,
                     json={"evento": "casual", "latitude": 0, "longitude": 0})
    assert r.status_code == 200 and r.json()["contexto"]["temperatura"] is None


# ------------------------------------------------------- feedback e métricas
def test_metricas_seguem_a_definicao(cliente, ana):
    """Fase 2, item 6. Três consultas: (1 aprovado, 1 rejeitado), (sem feedback),
    (2 rejeitados). Hit Rate@3 = 1/2; Precision@3 = 1/(3×2) — e não 1/4, que era
    aprovados ÷ feedbacks dados."""
    consultas = [cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()
                 for _ in range(3)]
    votar = lambda look, ok: cliente.post("/feedback", headers=ana,  # noqa: E731
                                          json={"look_id": look["id"], "aprovado": ok})
    assert votar(consultas[0]["looks"][0], True).status_code == 200
    votar(consultas[0]["looks"][1], False)
    votar(consultas[2]["looks"][0], False)
    votar(consultas[2]["looks"][1], False)

    m = cliente.get("/metricas", headers=ana).json()
    assert (m["consultas"], m["consultas_avaliadas"]) == (3, 2)
    assert (m["looks_mostrados"], m["looks_aprovados"]) == (9, 1)
    assert m["hit_rate_3"] == 0.5 and m["precision_3"] == round(1 / 6, 4)


def test_metricas_sao_por_usuario(cliente, ana, bruno):
    look = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"][0]
    cliente.post("/feedback", headers=ana, json={"look_id": look["id"], "aprovado": True})
    assert cliente.get("/metricas", headers=ana).json()["hit_rate_3"] == 1
    do_bruno = cliente.get("/metricas", headers=bruno).json()
    assert do_bruno["consultas"] == 0 and do_bruno["hit_rate_3"] is None
    # e o look de um não aceita feedback do outro
    assert cliente.post("/feedback", headers=bruno,
                        json={"look_id": look["id"], "aprovado": True}).status_code == 404


def test_feedback_ajusta_os_pesos_uma_vez_por_voto(cliente, ana):
    look = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"][0]
    corpo = {"look_id": look["id"], "aprovado": True}
    primeiro = cliente.post("/feedback", headers=ana, json=corpo).json()["pesos"]
    assert abs(sum(primeiro.values()) - 1) < 0.01 and all(v > 0 for v in primeiro.values())
    assert primeiro != {"ocasiao": 0.3, "clima": 0.25, "cor": 0.2, "estilo": 0.15, "variedade": 0.1}
    repetido = cliente.post("/feedback", headers=ana, json=corpo).json()["pesos"]
    assert repetido == primeiro                       # tocar de novo não reensina
    mudou = cliente.post("/feedback", headers=ana, json={**corpo, "aprovado": False}).json()["pesos"]
    assert mudou != primeiro


def test_look_sem_parcelas_nao_divide_por_zero(cliente, ana):
    """Fase 2, item 4."""
    look = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"][0]
    armazem.looks[look["id"]]["parcelas"] = {}
    r = cliente.post("/feedback", headers=ana, json={"look_id": look["id"], "aprovado": True})
    assert r.status_code == 200
    assert r.json()["pesos"] == {"ocasiao": 0.3, "clima": 0.25, "cor": 0.2,
                                 "estilo": 0.15, "variedade": 0.1}


def test_pesos_corrompidos_no_banco_voltam_ao_padrao(cliente, ana):
    """Fase 2, item 7 (lado da API; o banco tem a restrição equivalente)."""
    uid = cliente.get("/perfil", headers=ana).json()["id"]
    armazem.preferencias[uid] = {"pesos": {"ocasiao": -3, "clima": "x"}}
    assert cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).status_code == 200
    assert abs(sum(cliente.get("/perfil", headers=ana).json()["pesos"].values()) - 1) < 1e-9


def test_historico_longo_de_feedback_nao_quebra_a_recomendacao(cliente, ana):
    """Fase 2, item 3: a API mandava todos os IDs de look na URL."""
    for _ in range(40):
        looks = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"]
        for look in looks:
            cliente.post("/feedback", headers=ana, json={"look_id": look["id"], "aprovado": True})
    assert len(armazem.feedback) == 120
    assert cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).status_code == 200


def test_salvar_e_listar_looks(cliente, ana, bruno):
    look = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"}).json()["looks"][1]
    assert cliente.get("/looks?salvos=true", headers=ana).json() == []
    assert cliente.put(f"/looks/{look['id']}/salvo", headers=ana, json={"salvo": True}).json()["salvo"]
    salvos = cliente.get("/looks?salvos=true", headers=ana).json()
    assert [l["id"] for l in salvos] == [look["id"]]
    assert salvos[0]["pecas"] and salvos[0]["titulo"] == look["titulo"]
    assert len(cliente.get("/looks", headers=ana).json()) == 3
    assert cliente.put(f"/looks/{look['id']}/salvo", headers=bruno,
                       json={"salvo": True}).status_code == 404
    cliente.put(f"/looks/{look['id']}/salvo", headers=ana, json={"salvo": False})
    assert cliente.get("/looks?salvos=true", headers=ana).json() == []
