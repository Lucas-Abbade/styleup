"""Testes de extração e nomeação de cor.

A nomeação é requisito de acessibilidade (RNF05), não detalhe estético: é o que
um usuário com daltonismo lê no lugar da amostra colorida.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.cor import (
    cor_predominante,
    distancia_matiz,
    harmonia,
    hsv_para_hex,
    nomear,
    rgb_para_hsv,
)


# ------------------------------------------------------------------ nomeação
@pytest.mark.parametrize("rgb, esperado", [
    ((10, 10, 10), "preto"),
    ((250, 250, 250), "branco"),
    ((128, 128, 128), "cinza"),
    ((220, 30, 30), "vermelho"),
    ((30, 90, 200), "azul"),
    ((40, 160, 60), "verde"),
    ((240, 200, 40), "amarelo"),
    ((235, 140, 40), "laranja"),
    ((110, 70, 30), "marrom"),
    ((25, 35, 75), "marinho"),
    ((215, 195, 160), "bege"),
])
def test_nomes_de_cor(rgb, esperado):
    assert nomear(*rgb_para_hsv(*rgb))[0] == esperado


@pytest.mark.parametrize("rgb", [(10, 10, 10), (250, 250, 250), (128, 128, 128),
                                 (215, 195, 160), (25, 35, 75)])
def test_cores_neutras_sao_marcadas(rgb):
    assert nomear(*rgb_para_hsv(*rgb))[1] is True


def test_cor_saturada_nao_e_neutra():
    assert nomear(*rgb_para_hsv(220, 30, 30))[1] is False


def test_hex_reproduz_a_cor():
    assert hsv_para_hex(*rgb_para_hsv(220, 30, 30)) == "#dc1e1e"


# ---------------------------------------------------------------- extração
def _bloco(rgb, n):
    return np.tile(np.array(rgb, dtype=np.uint8), (n, 1))


def test_cor_predominante_em_imagem_uniforme():
    h, s, v = cor_predominante(_bloco((200, 30, 30), 500))
    assert nomear(h, s, v)[0] == "vermelho"


def test_predominante_vence_a_minoria():
    """70% azul, 30% amarelo: o resultado precisa ser azul."""
    pixels = np.vstack([_bloco((30, 60, 200), 700), _bloco((240, 220, 40), 300)])
    assert nomear(*cor_predominante(pixels))[0] == "azul"


def test_resultado_e_deterministico():
    pixels = np.vstack([_bloco((30, 60, 200), 400), _bloco((240, 220, 40), 200)])
    assert cor_predominante(pixels) == cor_predominante(pixels)


def test_sem_pixels_gera_erro_explicito():
    with pytest.raises(ValueError, match="segmentação"):
        cor_predominante(np.empty((0, 3), dtype=np.uint8))


# ---------------------------------------------------------------- harmonia
def test_distancia_de_matiz_atravessa_o_zero():
    assert distancia_matiz(350, 10) == 20
    assert distancia_matiz(10, 350) == 20


def test_neutro_com_cor_e_a_melhor_aposta():
    preto = ((0.0, 0.0, 0.05), True)
    azul = ((215.0, 0.7, 0.5), False)
    verde = ((120.0, 0.7, 0.5), False)
    assert harmonia(*preto, *azul) > harmonia(*azul, *verde)


def test_matizes_analogos_batem_conflito_intermediario():
    azul = ((215.0, 0.7, 0.5), False)
    ciano = ((190.0, 0.7, 0.5), False)
    verde = ((110.0, 0.7, 0.5), False)
    assert harmonia(*azul, *ciano) > harmonia(*azul, *verde)


def test_harmonia_e_simetrica():
    a = ((30.0, 0.8, 0.7), False)
    b = ((210.0, 0.6, 0.5), False)
    assert harmonia(*a, *b) == harmonia(*b, *a)


# --------------------------------------------------------------- concordância
@pytest.mark.parametrize("nome, genero, esperado", [
    ("branco", "f", "branca"),
    ("branco", "m", "branco"),
    ("preto", "f", "preta"),
    ("vermelho", "f", "vermelha"),
    ("azul", "f", "azul"),        # invariável
    ("verde", "f", "verde"),      # invariável
    ("bege", "f", "bege"),        # invariável
])
def test_concordancia_de_genero_da_cor(nome, genero, esperado):
    from app.services.cor import concordar
    assert concordar(nome, genero) == esperado


def test_toda_categoria_tem_genero_valido():
    from app.services.taxonomia import CATEGORIAS
    assert all(c.genero in ("m", "f") for c in CATEGORIAS)
