"""Testes de desempenho do motor (RNF02).

O requisito é recomendar em até 3 segundos com guarda-roupa de até 200 peças.
O produto cartesiano cresce com o produto dos três papéis, então sem corte o
número de candidatos explode. Estes testes travam esse comportamento: se alguém
remover o limite por papel, o tempo estoura aqui e não em produção.
"""

from __future__ import annotations

import time

from app.services.recomendador import (
    LIMITE_POR_PAPEL,
    Contexto,
    Peca,
    filtrar,
    gerar_combinacoes,
    recomendar,
)

CORES = [
    ((0.0, 0.0, 0.06), True),        # preto
    ((0.0, 0.0, 0.95), True),        # branco
    ((213.0, 0.65, 0.55), False),    # azul
    ((35.0, 0.22, 0.78), True),      # bege
    ((120.0, 0.55, 0.40), False),    # verde
]

MODELOS = [
    ("superior", "camiseta", 1, 18, 45),
    ("superior", "polo", 3, 18, 40),
    ("superior", "camisa-social", 5, 12, 35),
    ("superior", "sueter", 3, 2, 20),
    ("inferior", "bermuda", 1, 22, 45),
    ("inferior", "calca-jeans", 2, 8, 32),
    ("inferior", "calca-social", 5, 8, 32),
    ("calcado", "tenis", 2, 0, 45),
    ("calcado", "sapato-social", 5, 0, 40),
    ("calcado", "bota", 3, 0, 28),
    ("sobreposicao", "jaqueta-jeans", 2, 8, 22),
    ("sobreposicao", "blazer", 5, 8, 24),
]


def acervo(quantidade: int) -> list[Peca]:
    """Acervo sintético grande, variado em papel, formalidade, cor e faixa térmica."""
    pecas = []
    for i in range(quantidade):
        papel, categoria, formalidade, tmin, tmax = MODELOS[i % len(MODELOS)]
        cor, neutra = CORES[i % len(CORES)]
        pecas.append(Peca(
            id=f"p{i}", papel=papel, categoria=categoria, formalidade=formalidade,
            cor_hsv=cor, neutra=neutra, temp_min=tmin, temp_max=tmax,
            usos_recentes=i % 4,
        ))
    return pecas


def test_corte_limita_o_numero_de_candidatos():
    """Com 200 peças, o motor avalia milhares de candidatos, não centenas de milhares."""
    ctx = Contexto(formalidade_alvo=3, temperatura=22)
    grupos = filtrar(acervo(200), ctx)

    sem_corte = 1
    for papel in ("superior", "inferior", "calcado"):
        sem_corte *= max(len(grupos[papel]), 1)

    candidatos = gerar_combinacoes(grupos, ctx)

    assert sem_corte > 10_000                       # o problema é real
    assert len(candidatos) <= LIMITE_POR_PAPEL ** 3  # e está contido


def test_duzentas_pecas_recomendam_dentro_do_orcamento():
    """RNF02: 3 s é o limite; medimos com folga grande para não ficar instável em CI."""
    pecas = acervo(200)
    ctx = Contexto(formalidade_alvo=3, temperatura=20, chuva_prob=0.2)

    inicio = time.perf_counter()
    looks = recomendar(pecas, ctx)
    duracao = time.perf_counter() - inicio

    assert len(looks) == 3
    assert duracao < 1.0, f"recomendação levou {duracao:.2f}s"


def test_corte_preserva_a_qualidade_do_melhor_look():
    """O corte não pode custar qualidade: comparamos com o motor sem limite.

    Se a melhor peça de um papel não está entre as doze mais ajustadas ao
    contexto, o corte estaria descartando algo relevante — e o teste falharia.
    """
    pecas = acervo(120)
    ctx = Contexto(formalidade_alvo=3, temperatura=22)

    com_corte = recomendar(pecas, ctx)[0]

    grupos = filtrar(pecas, ctx)
    total = max(len(grupos[p]) for p in ("superior", "inferior", "calcado"))
    exaustivo = gerar_combinacoes(grupos, ctx, limite_por_papel=total)
    from app.services.recomendador import PESOS_PADRAO, pontuar
    melhor_possivel = max(
        (pontuar(l, ctx, PESOS_PADRAO).score for l in exaustivo), default=0.0)

    assert com_corte.score >= melhor_possivel - 0.02


def test_acervo_grande_com_contexto_impossivel_falha_rapido():
    """Nenhuma peça serve a -10 °C: o erro precisa vir na hora, não depois de pontuar."""
    from app.services.recomendador import SemPecasSuficientes
    import pytest

    pecas = acervo(200)
    inicio = time.perf_counter()
    with pytest.raises(SemPecasSuficientes):
        recomendar(pecas, Contexto(formalidade_alvo=3, temperatura=-10))
    assert time.perf_counter() - inicio < 0.2
