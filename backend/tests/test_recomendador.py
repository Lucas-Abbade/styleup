"""Testes do motor de recomendação.

Cada teste isola uma regra. Quando a banca perguntar "por que este look e não
aquele", a resposta está aqui, não numa explicação improvisada.
"""

from __future__ import annotations

import pytest

from app.services.recomendador import (
    Contexto,
    Peca,
    PESOS_PADRAO,
    SemPecasSuficientes,
    ajustar_pesos,
    filtrar,
    gerar_combinacoes,
    passa_filtros,
    recomendar,
)

PRETO = (0.0, 0.0, 0.05)
BRANCO = (0.0, 0.0, 0.95)
AZUL = (215.0, 0.7, 0.5)
LARANJA = (25.0, 0.8, 0.8)
VERDE = (120.0, 0.7, 0.5)


def peca(id, papel, categoria="x", formalidade=3, cor=PRETO, neutra=True,
         temp_min=0, temp_max=45, chuva=True, disponivel=True, usos=0):
    return Peca(id=id, papel=papel, categoria=categoria, formalidade=formalidade,
                cor_hsv=cor, neutra=neutra, temp_min=temp_min, temp_max=temp_max,
                resiste_chuva=chuva, disponivel=disponivel, usos_recentes=usos)


def acervo_basico():
    """Guarda-roupa pequeno, porém completo: cobre as três faixas de formalidade
    e as duas de temperatura, para que os testes exercitem escolha e não escassez.
    """
    return [
        peca("s1", "superior", "camiseta", 2, BRANCO, True, 18, 45),
        peca("s2", "superior", "polo", 3, AZUL, False, 18, 40),
        peca("s3", "superior", "camisa-social", 5, BRANCO, True, 12, 35),
        peca("s4", "superior", "sueter", 3, PRETO, True, 2, 20),
        peca("i1", "inferior", "calca-jeans", 2, AZUL, False, 8, 32),
        peca("i2", "inferior", "calca-sarja", 3, PRETO, True, 8, 32),
        peca("i3", "inferior", "calca-social", 5, PRETO, True, 8, 32),
        peca("c1", "calcado", "tenis", 2, BRANCO, True, 0, 45),
        peca("c2", "calcado", "tenis-casual", 3, PRETO, True, 0, 45),
        peca("c3", "calcado", "sapato-social", 5, PRETO, True, 0, 40),
        peca("c4", "calcado", "chinelo", 1, PRETO, True, 24, 45, chuva=False),
        peca("j1", "sobreposicao", "casaco", 3, PRETO, True, -5, 16),
        peca("j2", "sobreposicao", "blazer", 5, PRETO, True, 8, 24),
    ]


# ------------------------------------------------------------ filtros rígidos
def test_peca_indisponivel_e_descartada():
    p = peca("x", "superior", disponivel=False)
    assert not passa_filtros(p, Contexto(formalidade_alvo=3))


def test_peca_fora_da_faixa_de_temperatura_e_descartada():
    bermuda = peca("b", "inferior", temp_min=22, temp_max=45)
    assert not passa_filtros(bermuda, Contexto(formalidade_alvo=2, temperatura=10))
    assert passa_filtros(bermuda, Contexto(formalidade_alvo=2, temperatura=30))


def test_tolerancia_de_tres_graus_na_faixa():
    """A faixa da taxonomia é média, não fronteira: 3 °C de folga são aceitos."""
    bermuda = peca("b", "inferior", temp_min=22, temp_max=45)
    assert passa_filtros(bermuda, Contexto(formalidade_alvo=2, temperatura=19.5))
    assert not passa_filtros(bermuda, Contexto(formalidade_alvo=2, temperatura=18))


def test_chinelo_sai_quando_chove():
    chinelo = peca("c", "calcado", formalidade=1, chuva=False, temp_min=24)
    seco = Contexto(formalidade_alvo=1, temperatura=30, chuva_prob=0.1)
    molhado = Contexto(formalidade_alvo=1, temperatura=30, chuva_prob=0.8)
    assert passa_filtros(chinelo, seco)
    assert not passa_filtros(chinelo, molhado)


def test_formalidade_admite_um_ponto_de_folga():
    social = peca("s", "superior", formalidade=5)
    assert passa_filtros(social, Contexto(formalidade_alvo=4))
    assert not passa_filtros(social, Contexto(formalidade_alvo=3))


def test_sensacao_termica_tem_prioridade_sobre_temperatura():
    ctx = Contexto(formalidade_alvo=3, temperatura=25, sensacao=12)
    assert ctx.temperatura_efetiva == 12
    camiseta = peca("t", "superior", temp_min=18, temp_max=45)
    assert not passa_filtros(camiseta, ctx)


# ---------------------------------------------------------------- combinações
def test_combinacoes_sao_o_produto_dos_tres_papeis():
    grupos = filtrar(acervo_basico(), Contexto(formalidade_alvo=2, temperatura=25))
    looks = gerar_combinacoes(grupos, Contexto(formalidade_alvo=2, temperatura=25))
    esperado = len(grupos["superior"]) * len(grupos["inferior"]) * len(grupos["calcado"])
    assert len(looks) == esperado
    assert all("sobreposicao" not in l.pecas for l in looks)


def test_frio_traz_a_sobreposicao_para_o_look():
    ctx = Contexto(formalidade_alvo=3, temperatura=10)
    grupos = filtrar(acervo_basico(), ctx)
    looks = gerar_combinacoes(grupos, ctx)
    assert looks and all("sobreposicao" in l.pecas for l in looks)


def test_sem_casaco_no_acervo_ainda_recomenda():
    """Não ter agasalho não pode zerar a recomendação; o RNF07 pede degradação."""
    acervo = [p for p in acervo_basico() if p.papel != "sobreposicao"]
    ctx = Contexto(formalidade_alvo=5, temperatura=10)
    looks = recomendar(acervo, ctx)
    assert looks
    assert all("sobreposicao" not in l.pecas for l in looks)


# --------------------------------------------------------------------- score
def test_look_coerente_vence_look_desconexo():
    """Blazer com chinelo tem formalidade média aceitável, mas dispersão alta."""
    acervo = [
        peca("s", "superior", "camisa-social", 5, BRANCO),
        peca("i", "inferior", "calca-social", 5, PRETO),
        peca("bom", "calcado", "sapato-social", 5, PRETO),
        peca("ruim", "calcado", "chinelo", 4, PRETO),   # formalidade forçada p/ passar o filtro
    ]
    looks = recomendar(acervo, Contexto(formalidade_alvo=5, temperatura=25), quantidade=2)
    assert looks[0].pecas["calcado"].id == "bom"


def test_harmonia_de_cor_desempata():
    acervo = [
        peca("s", "superior", "camiseta", 2, AZUL, neutra=False, temp_min=18),
        peca("harmonico", "inferior", "calca-jeans", 2, PRETO, neutra=True, temp_min=8),
        peca("conflito", "inferior", "calca-sarja", 2, VERDE, neutra=False, temp_min=8),
        peca("c", "calcado", "tenis", 2, BRANCO, neutra=True),
    ]
    looks = recomendar(acervo, Contexto(formalidade_alvo=2, temperatura=25), quantidade=2)
    assert looks[0].pecas["inferior"].id == "harmonico"


def test_peca_muito_usada_perde_para_peca_nova():
    acervo = [
        peca("s", "superior", "camiseta", 2, BRANCO, temp_min=18),
        peca("i", "inferior", "calca-jeans", 2, PRETO, temp_min=8),
        peca("nova", "calcado", "tenis", 2, BRANCO, usos=0),
        peca("gasta", "calcado", "tenis", 2, BRANCO, usos=5),
    ]
    looks = recomendar(acervo, Contexto(formalidade_alvo=2, temperatura=25), quantidade=2)
    assert looks[0].pecas["calcado"].id == "nova"


def test_score_fica_entre_zero_e_um():
    looks = recomendar(acervo_basico(), Contexto(formalidade_alvo=2, temperatura=25))
    assert all(0.0 <= l.score <= 1.0 for l in looks)


# ---------------------------------------------------------------- resultado
def test_devolve_tres_looks():
    looks = recomendar(acervo_basico(), Contexto(formalidade_alvo=2, temperatura=25))
    assert len(looks) == 3


def test_acervo_pequeno_devolve_o_que_existe():
    """Com duas combinações possíveis, devolvemos duas — e não um erro.

    Um guarda-roupa recém-cadastrado é o caso comum no primeiro uso; exigir três
    opções afastaria o usuário logo no início.
    """
    acervo = [
        peca("s", "superior", "camiseta", 2, BRANCO, temp_min=18),
        peca("i", "inferior", "calca-jeans", 2, PRETO, temp_min=8),
        peca("c1", "calcado", "tenis", 2, BRANCO),
        peca("c2", "calcado", "tenis-casual", 3, PRETO),
    ]
    looks = recomendar(acervo, Contexto(formalidade_alvo=2, temperatura=25))
    assert len(looks) == 2


def test_looks_sao_diversificados():
    """Três variações da mesma camiseta valeriam por uma no Hit Rate@3."""
    acervo = [
        peca(f"s{i}", "superior", "camiseta", 2, BRANCO, temp_min=18) for i in range(3)
    ] + [
        peca(f"i{i}", "inferior", "calca-jeans", 2, PRETO, temp_min=8) for i in range(3)
    ] + [
        peca(f"c{i}", "calcado", "tenis", 2, BRANCO) for i in range(3)
    ]
    looks = recomendar(acervo, Contexto(formalidade_alvo=2, temperatura=25))
    assert len({tuple(sorted(l.ids)) for l in looks}) == 3


def test_erro_claro_quando_falta_papel_obrigatorio():
    acervo = [peca("s", "superior"), peca("i", "inferior")]
    with pytest.raises(SemPecasSuficientes) as exc:
        recomendar(acervo, Contexto(formalidade_alvo=3))
    assert "calcado" in exc.value.papeis


def test_sem_dados_de_clima_ainda_recomenda():
    looks = recomendar(acervo_basico(), Contexto(formalidade_alvo=2))
    assert len(looks) == 3


# ----------------------------------------------------------- ajuste de pesos
def test_aprovacao_reforca_o_criterio_dominante():
    parcelas = {"ocasiao": 0.9, "clima": 0.5, "cor": 0.5, "estilo": 0.5, "variedade": 0.5}
    novos = ajustar_pesos(dict(PESOS_PADRAO), parcelas, aprovado=True)
    assert novos["ocasiao"] > PESOS_PADRAO["ocasiao"]


def test_rejeicao_reduz_o_criterio_dominante():
    parcelas = {"ocasiao": 0.9, "clima": 0.5, "cor": 0.5, "estilo": 0.5, "variedade": 0.5}
    novos = ajustar_pesos(dict(PESOS_PADRAO), parcelas, aprovado=False)
    assert novos["ocasiao"] < PESOS_PADRAO["ocasiao"]


def test_pesos_permanecem_normalizados_e_positivos():
    pesos = dict(PESOS_PADRAO)
    parcelas = {"ocasiao": 0.9, "clima": 0.1, "cor": 0.8, "estilo": 0.2, "variedade": 0.4}
    for i in range(50):
        pesos = ajustar_pesos(pesos, parcelas, aprovado=i % 2 == 0)
    assert abs(sum(pesos.values()) - 1.0) < 0.01
    assert all(v > 0 for v in pesos.values())
