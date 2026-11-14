"""Script de acurácia (fase 4, item 1): a parte de leitura, contagem e relatório."""

from __future__ import annotations

import pytest

from scripts.medir_acuracia import avaliar, ler_rotulos, relatorio_markdown, wilson

CSV = """arquivo,categoria,cor,estilo,manga,estampa
a.jpg,camiseta,preto,esportivo,curta,lisa
b.jpg,camiseta,branco,esportivo,curta,
c.jpg,calca-jeans,azul,casual,,lisa
d.jpg,tenis,branco,casual,,
sumiu.jpg,polo,marinho,casual-arrumado,curta,lisa
ruim.jpg,polo,marinho,,,
"""

RESPOSTAS = {
    b"a": ("camiseta", "preto", 1, {"manga": "curta", "estampa": "lisa"}),
    b"b": ("polo", "branco", 3, {"manga": "curta", "estampa": "lisa"}),       # categoria errada
    b"c": ("calca-jeans", "marinho", 2, {"manga": "longa", "estampa": "lisa"}),  # cor errada
    b"d": ("tenis", "branco", 2, {}),
}


@pytest.fixture
def pasta(tmp_path):
    (tmp_path / "rotulos.csv").write_text(CSV, encoding="utf-8")
    fotos = tmp_path / "fotos"
    fotos.mkdir()
    for nome in ("a", "b", "c", "d"):
        (fotos / f"{nome}.jpg").write_bytes(nome.encode())
    (fotos / "ruim.jpg").write_bytes(b"x")
    return tmp_path


def analisar(dados: bytes) -> dict:
    if dados == b"x":
        raise ValueError("A foto parece borrada.")
    categoria, cor, formalidade, atributos = RESPOSTAS[dados]
    return {"categoria": categoria, "cor_nome": cor, "formalidade": formalidade,
            "atributos": atributos, "confianca": {categoria: 0.8, "camiseta": 0.1},
            "confianca_baixa": dados == b"b"}


def test_relatorio_por_atributo(pasta):
    r = avaliar(ler_rotulos(pasta / "rotulos.csv"), pasta / "fotos", analisar)
    assert (r["total_rotuladas"], r["analisadas"], len(r["falhas"])) == (6, 4, 2)
    assert {f["arquivo"] for f in r["falhas"]} == {"sumiu.jpg", "ruim.jpg"}

    categoria = r["atributos"]["categoria"]
    assert (categoria["acertos"], categoria["avaliadas"], categoria["acuracia"]) == (3, 4, 0.75)
    assert categoria["top3"] == 1.0                     # a camiseta errada estava no top-3
    assert categoria["por_classe"]["camiseta"] == {"acertos": 1, "total": 2}
    assert categoria["confusoes"] == [{"esperado": "camiseta", "previsto": "polo", "vezes": 1}]
    assert r["atributos"]["cor"]["acuracia"] == 0.75
    # colunas vazias não entram na conta daquele atributo
    assert r["atributos"]["manga"]["avaliadas"] == 2 and r["atributos"]["estampa"]["avaliadas"] == 2
    assert r["atributos"]["estilo"]["acertos"] == 3
    assert r["confianca_baixa"] == 1 and r["tempo"]["mediana_s"] is not None

    texto = relatorio_markdown(r)
    assert "| categoria | 4 | 3 | 75,0% |" in texto
    assert "inconclusivo (amostra pequena)" in texto     # 4 fotos não provam 90%
    assert "camiseta → classificada como **polo** (1×)" in texto
    assert "`ruim.jpg` — A foto parece borrada." in texto


def test_wilson():
    baixo, alto = wilson(80, 100)
    assert 0.71 < baixo < 0.72 and 0.86 < alto < 0.87
    assert wilson(0, 0) == (0.0, 0.0)
    assert wilson(10, 10)[0] < 1.0 and wilson(10, 10)[1] == 1.0


def test_rotulos_invalidos_sao_apontados_por_linha(tmp_path):
    (tmp_path / "rotulos.csv").write_text(
        "arquivo,categoria,cor,estilo,manga,estampa\n"
        "a.jpg,chapeu,preto,,,\n"
        "b.jpg,camiseta,azul-piscina,chique,media,\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        ler_rotulos(tmp_path / "rotulos.csv")
    texto = str(exc.value)
    assert "linha 2: categoria desconhecida 'chapeu'" in texto
    assert "linha 3: cor desconhecida" in texto and "estilo desconhecido" in texto
    assert "manga desconhecida" in texto
