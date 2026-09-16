"""Testes do tratamento global de erros.

O que garantem: nenhuma falha previsível chega ao usuário como lista de objetos
em inglês ou como 500 sem rastro, e toda resposta de erro carrega o mesmo
envelope com um id que existe no log.
"""

from __future__ import annotations

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.erros import CABECALHO_REQUISICAO
from app.main import app


# ------------------------------------------------------------- envelope
def test_todo_erro_tem_detail_e_id_de_requisicao(cliente):
    resposta = cliente.post("/recomendacoes", json={"evento": "inexistente"})
    corpo = resposta.json()
    assert resposta.status_code == 422
    assert isinstance(corpo["detail"], str)
    assert corpo["requisicao"]
    assert resposta.headers[CABECALHO_REQUISICAO] == corpo["requisicao"]


def test_id_da_requisicao_e_diferente_a_cada_chamada(cliente):
    a = cliente.get("/saude").headers[CABECALHO_REQUISICAO]
    b = cliente.get("/saude").headers[CABECALHO_REQUISICAO]
    assert a != b


def test_404_tambem_segue_o_envelope(cliente):
    resposta = cliente.get("/rota-que-nao-existe")
    assert resposta.status_code == 404
    assert "requisicao" in resposta.json()


# --------------------------------------------------- validação em português
def test_erro_de_validacao_vem_em_portugues_e_nomeia_o_campo(cliente):
    """Antes chegava `[{"loc":["body","formalidade"],"msg":"Input should be..."}]`."""
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "superior", "formalidade": 99,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
    })
    detalhe = resposta.json()["detail"]
    assert resposta.status_code == 422
    assert detalhe.startswith("Dados inválidos")
    assert "formalidade" in detalhe
    assert "valor máximo" in detalhe
    assert "Input should" not in detalhe          # nada de inglês cru


def test_campo_obrigatorio_ausente_e_nomeado(cliente):
    resposta = cliente.post("/pecas", json={"categoria": "camiseta"})
    detalhe = resposta.json()["detail"]
    assert "papel" in detalhe or "cor_nome" in detalhe
    assert "obrigatório" in detalhe


# ------------------------------------------------- validação estrita (extra)
def test_campo_desconhecido_e_recusado(cliente):
    """`corHex` em vez de `cor_hex` gravava peça sem cor, em silêncio."""
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "superior", "formalidade": 2,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
        "corHex": "#ffffff",
    })
    assert resposta.status_code == 422
    assert "corHex" in resposta.json()["detail"]


def test_cor_hex_invalida_e_recusada(cliente):
    """O valor vai para o atributo style do frontend; texto livre seria injeção."""
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "superior", "formalidade": 2,
        "cor_nome": "azul", "cor_hex": "red; background:url(javascript:0)",
        "cor_hsv": [213, 0.7, 0.62],
    })
    assert resposta.status_code == 422
    assert "cor_hex" in resposta.json()["detail"]


def test_cor_hsv_com_tamanho_errado_e_recusada(cliente):
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "superior", "formalidade": 2,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7],
    })
    assert resposta.status_code == 422
    assert "cor_hsv" in resposta.json()["detail"]


def test_faixa_termica_invertida_e_recusada(cliente):
    """temp_min > temp_max deixaria a peça fora de todo filtro, para sempre."""
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "superior", "formalidade": 2,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
        "temp_min": 40, "temp_max": 10,
    })
    assert resposta.status_code == 422
    assert "temp_min" in resposta.json()["detail"]


def test_papel_invalido_lista_as_opcoes(cliente):
    resposta = cliente.post("/pecas", json={
        "categoria": "camiseta", "papel": "chapeu", "formalidade": 2,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
    })
    assert resposta.status_code == 422
    assert "papel" in resposta.json()["detail"]


# ------------------------------------------------------- rede de segurança
def test_excecao_inesperada_vira_500_tratado(caplog):
    """Rede de segurança: sem mensagem interna na tela, com id no log."""
    rota = APIRouter()

    @rota.get("/_falha_proposital")
    def falhar():
        raise RuntimeError("segredo interno que não pode aparecer na tela")

    app.include_router(rota)
    try:
        # raise_server_exceptions=False faz o TestClient exercitar o handler em
        # vez de propagar a exceção para o pytest
        with TestClient(app, raise_server_exceptions=False) as c:
            resposta = c.get("/_falha_proposital")
        assert resposta.status_code == 500
        corpo = resposta.json()
        assert corpo["detail"] == ("Erro interno no servidor. "
                                   "Tente novamente em instantes.")
        assert "segredo interno" not in resposta.text
        assert corpo["requisicao"]
    finally:
        app.router.routes = [r for r in app.router.routes
                             if getattr(r, "path", None) != "/_falha_proposital"]


@pytest.mark.parametrize("payload", [
    {},
    {"evento": None},
    {"evento": ""},
    {"evento": "casual", "temperatura": "quente"},
    {"evento": "casual", "latitude": 200},
    {"evento": "casual", "chuva_prob": 5},
    {"evento": "casual", "extra": 1},
])
def test_nenhum_corpo_malformado_gera_500(cliente, payload):
    resposta = cliente.post("/recomendacoes", json=payload)
    assert resposta.status_code == 422, resposta.text
    assert isinstance(resposta.json()["detail"], str)
