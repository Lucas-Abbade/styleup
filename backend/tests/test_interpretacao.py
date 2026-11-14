"""Interpretação do pedido em texto livre."""

from __future__ import annotations

import pytest

from app.services.interpretacao import interpretar


@pytest.mark.parametrize("texto, evento, estilo, temperatura", [
    ("Look para a faculdade, casual, all black", "faculdade", "all-black", None),
    ("quero algo minimalista pro trabalho", "trabalho", "minimalista", None),
    ("ENTREVISTA de estágio amanhã", "reuniao", None, None),
    ("rolê à noite, 18°C", "balada", None, 18),
    ("treino na academia", "academia", None, None),
    ("praia no verão", "praia", None, 32),
    ("dia frio, tons terrosos", None, "terroso", 12),
    ("casamento da minha prima", "formal", None, None),
    ("algo esportivo", "academia", "esportivo", None),
    ("streetwear pra dar um passeio no shopping", "casual", "urbano", None),
    ("jantar, 22 graus", "jantar", None, 22),
    ("faz -3 graus aqui", None, None, -3),
    ("", None, None, None),
    ("asdf qwer", None, None, None),
])
def test_interpretacao(texto, evento, estilo, temperatura):
    r = interpretar(texto)
    assert (r.evento, r.estilo, r.temperatura) == (evento, estilo, temperatura)


def test_chuva_e_rotulos_do_que_foi_entendido():
    r = interpretar("Reunião no escritório, dia chuvoso, 19 graus, visual clássico")
    assert r.chuva is True
    assert r.entendido == ["Reunião ou entrevista", "Clássico", "19 °C", "chuva"]


def test_palavra_dentro_de_outra_nao_dispara():
    assert interpretar("barbante").evento is None          # "bar"
    assert interpretar("solteiro").temperatura is None     # "sol"
    assert interpretar("all black").evento is None         # não é "black tie"


def test_temperatura_absurda_e_texto_gigante_sao_ignorados():
    assert interpretar("99 graus").temperatura is None
    assert interpretar("x" * 5000 + " faculdade").evento is None      # corta em 300
