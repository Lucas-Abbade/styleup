"""Regras novas do motor: precisão dos looks, degradação e desempenho."""

from __future__ import annotations

import time

from app.repositorio.memoria import peca_de_exemplo
from app.services import explicacao
from app.services.cor import harmonia, hex_para_hsv, luminosidade, nomear
from app.services.recomendador import (
    TOP_N_POR_PAPEL, Contexto, Peca, _conforto, ajustar_pesos, normalizar_pesos,
    nota_estilo_pedido, peca_de_linha, pesos_validos, pontuar, recomendar,
    recomendar_com_avisos, taxa_suavizada,
)


def peca(id, categoria, cor, **extras) -> Peca:
    return peca_de_linha({"id": id, **peca_de_exemplo(categoria, cor), **extras})


def acervo(*itens) -> list[Peca]:
    return [peca(f"{c}-{cor}", c, cor) for c, cor in itens]


BASE = [("camiseta", "branco"), ("camiseta", "preto"), ("polo", "marinho"),
        ("camisa-social", "branco"), ("moletom", "cinza"),
        ("bermuda", "bege"), ("calca-jeans", "azul"), ("calca-sarja", "cáqui"),
        ("calca-social", "grafite"), ("tenis", "branco"), ("tenis-casual", "preto"),
        ("sapato-social", "preto"), ("chinelo", "preto"),
        ("jaqueta-jeans", "azul"), ("blazer", "marinho"), ("casaco", "preto")]


# ----------------------------------------------------------------- cor
def test_jeans_azul_funciona_como_neutro():
    """Camiseta verde com jeans azul é combinação corriqueira; pela distância de
    matiz (≈95°) caía na "zona de conflito" e perdia para qualquer calça preta."""
    com_jeans = acervo(("camiseta", "verde"), ("calca-jeans", "azul"), ("tenis", "branco"))
    com_sarja_azul = [peca("s", "camiseta", "verde"), peca("i", "calca-sarja", "azul"),
                      peca("c", "tenis", "branco")]
    ctx = Contexto(formalidade_alvo=2, temperatura=25)
    nota_jeans = recomendar(com_jeans, ctx)[0].parcelas["cor"]
    nota_sarja = recomendar(com_sarja_azul, ctx)[0].parcelas["cor"]
    assert nota_jeans > 0.9 > nota_sarja


def test_cores_apagadas_brigam_menos_que_cores_vivas():
    vivo = harmonia((0, 1, 1), False, (120, 1, 1), False)
    apagado = harmonia((0, 0.3, 0.6), False, (120, 0.3, 0.6), False)
    assert apagado > vivo + 0.2


def test_complementar_nao_ganha_bonus():
    """Schloss & Palmer (2011): harmonia cai com a distância de matiz, sem alta
    nos opostos. O degrau "complementar = 0,70" não tinha base medida."""
    analogo = harmonia((30, 0.8, 0.8), False, (60, 0.8, 0.8), False)
    conflito = harmonia((30, 0.8, 0.8), False, (120, 0.8, 0.8), False)
    oposto = harmonia((30, 0.8, 0.8), False, (210, 0.8, 0.8), False)
    assert analogo > conflito and oposto <= conflito + 0.06


def test_contraste_de_claridade_ajuda():
    preto, branco, quase_preto = (0, 0, 0.10), (0, 0, 0.96), (0, 0, 0.17)
    assert harmonia(preto, True, branco, True) > harmonia(preto, True, quase_preto, True)
    # preto com preto é intenção; preto com "quase preto" parece engano
    assert harmonia(preto, True, preto, True) > harmonia(preto, True, quase_preto, True)
    assert luminosidade(60, 1, 1) > luminosidade(240, 1, 1) + 50    # amarelo × azul


def test_mais_de_dois_matizes_e_estampas_demais_sao_penalizados():
    ctx = Contexto(formalidade_alvo=2, temperatura=25)
    discreto = recomendar(acervo(("camiseta", "vermelho"), ("calca-sarja", "bege"),
                                 ("tenis", "branco")), ctx)[0]
    carnaval = recomendar(acervo(("camiseta", "vermelho"), ("calca-sarja", "verde"),
                                 ("tenis", "roxo")), ctx)[0]
    assert discreto.parcelas["cor"] > carnaval.parcelas["cor"] + 0.3

    lisas = [peca("s", "camiseta", "branco"), peca("i", "bermuda", "bege"),
             peca("c", "tenis", "preto")]
    estampadas = [peca("s", "camiseta", "branco", atributos={"estampa": "listrada"}),
                  peca("i", "bermuda", "bege", atributos={"estampa": "xadrez"}),
                  peca("c", "tenis", "preto")]
    assert recomendar(lisas, ctx)[0].parcelas["cor"] > recomendar(estampadas, ctx)[0].parcelas["cor"]


def test_nomes_de_cor_do_vestuario():
    esperado = {"#6b7340": "verde-oliva", "#3d3d40": "grafite", "#b09a6b": "cáqui",
                "#6e1f2b": "vinho", "#1c2a4a": "marinho", "#9cc3e6": "azul-claro",
                "#b5651d": "caramelo", "#c99a1e": "mostarda", "#d9c6a3": "bege"}
    for cor_hex, nome in esperado.items():
        assert nomear(*hex_para_hsv(cor_hex))[0] == nome, cor_hex


# --------------------------------------------------------------- clima
def test_camiseta_dentro_da_faixa_nao_e_punida():
    """Antes: 0,15 para uma camiseta (18–45 °C) num dia de 20 °C."""
    camiseta = peca("s", "camiseta", "branco")
    assert _conforto(camiseta, 20) > 0.5
    assert _conforto(camiseta, 30) > _conforto(camiseta, 20) > _conforto(camiseta, 14)


def test_no_calor_bermuda_vence_calca_e_no_frio_o_contrario():
    pecas = acervo(("camiseta", "branco"), ("bermuda", "bege"), ("calca-jeans", "azul"),
                   ("tenis", "branco"))
    quente = recomendar(pecas, Contexto(formalidade_alvo=2, temperatura=34))[0]
    ameno = recomendar(pecas, Contexto(formalidade_alvo=2, temperatura=20))[0]
    assert quente.pecas["inferior"].categoria == "bermuda"
    assert ameno.pecas["inferior"].categoria == "calca-jeans"


# ---------------------------------------------------------- degradação
def test_degradacao_afrouxa_so_o_papel_que_faltou_e_avisa():
    """RNF07: 9 °C e só camiseta como parte de cima. Antes: 409."""
    pecas = acervo(("camiseta", "branco"), ("calca-jeans", "azul"), ("tenis", "preto"))
    resultado = recomendar_com_avisos(pecas, Contexto(formalidade_alvo=2, temperatura=9))
    assert len(resultado.looks) == 1
    assert any("parte de cima" in a for a in resultado.avisos)
    assert not any("parte de baixo" in a for a in resultado.avisos)
    assert any("agasalho" in a for a in resultado.avisos)


def test_sem_degradacao_nao_ha_aviso():
    resultado = recomendar_com_avisos(acervo(*BASE), Contexto(formalidade_alvo=2, temperatura=25))
    assert len(resultado.looks) == 3 and resultado.avisos == []


# ------------------------------------------------- evento, estilo, extras
def test_evento_distingue_casa_de_academia():
    pecas = acervo(("camiseta", "branco"), ("bermuda", "bege"), ("tenis", "branco"),
                   ("chinelo", "preto"))
    treino = recomendar(pecas, Contexto(formalidade_alvo=1, temperatura=28, evento="academia"))
    casa = recomendar(pecas, Contexto(formalidade_alvo=1, temperatura=28, evento="casa"))
    assert all(l.pecas["calcado"].categoria == "tenis" for l in treino)
    assert casa[0].pecas["calcado"].categoria == "chinelo"


def test_blazer_completa_o_traje_social_mesmo_sem_frio():
    pecas = acervo(("camisa-social", "branco"), ("calca-social", "grafite"),
                   ("sapato-social", "preto"), ("blazer", "marinho"))
    social = recomendar(pecas, Contexto(formalidade_alvo=5, temperatura=23, evento="formal"))[0]
    assert social.pecas.get("sobreposicao") and social.pecas["sobreposicao"].categoria == "blazer"
    calor = recomendar(pecas, Contexto(formalidade_alvo=5, temperatura=33, evento="formal"))[0]
    assert "sobreposicao" not in calor.pecas


def test_estilo_pedido_muda_o_look():
    ctx = dict(formalidade_alvo=2, temperatura=25)
    pecas = acervo(*BASE, ("camiseta", "vermelho"), ("tenis", "preto"), ("calca-jeans", "preto"))
    preto = recomendar(pecas, Contexto(**ctx, estilo="all-black"))[0]
    assert nota_estilo_pedido(preto, "all-black") == 1.0
    cor = recomendar(pecas, Contexto(**ctx, estilo="colorido"))[0]
    assert any(not p.neutra for p in cor.pecas.values())
    assert explicacao.titulo(preto, Contexto(**ctx, estilo="all-black")).endswith("All black")


def test_acessorios_entram_sem_mudar_o_score_e_respeitam_regras():
    pecas = acervo(*BASE, ("bone", "grafite"), ("cinto", "preto"), ("relogio", "preto"),
                   ("gorro", "preto"), ("calca-moletom", "grafite"))
    ctx = Contexto(formalidade_alvo=2, temperatura=26, evento="casual")
    com = recomendar(pecas, ctx)
    sem = recomendar([p for p in pecas if p.papel != "acessorio"], ctx)
    assert [round(l.score, 6) for l in com] == [round(l.score, 6) for l in sem]
    for look in com:
        assert len(look.acessorios) <= 2
        assert len({a.categoria for a in look.acessorios}) == len(look.acessorios)
        assert all(a.categoria != "gorro" for a in look.acessorios)        # 26 °C
        if look.pecas["inferior"].categoria == "calca-moletom":
            assert all(a.categoria != "cinto" for a in look.acessorios)
    assert any(look.acessorios for look in com)
    assert set(com[0].ids) >= {a.id for a in com[0].acessorios}


def test_looks_nao_repetem_a_mesma_dupla_de_cima_e_de_baixo():
    looks = recomendar(acervo(*BASE), Contexto(formalidade_alvo=2, temperatura=25))
    duplas = {(l.pecas["superior"].id, l.pecas["inferior"].id) for l in looks}
    assert len(duplas) == 3


# ---------------------------------------------------------- explicação
def test_texto_do_frio_bate_com_a_regra_do_motor():
    """Fase 2, item 10: o motor exige sobreposição abaixo de 18 °C, mas o texto
    só dizia "pedem agasalho" abaixo de 15 °C — e dizia mesmo sem agasalho."""
    com_casaco = acervo(("moletom", "cinza"), ("calca-jeans", "azul"), ("tenis", "preto"),
                        ("jaqueta-jeans", "azul"))
    ctx = Contexto(formalidade_alvo=2, temperatura=17)
    look = recomendar(com_casaco, ctx)[0]
    assert "pedem agasalho" in explicacao.por_template(look, ctx)

    sem_casaco = [p for p in com_casaco if p.papel != "sobreposicao"]
    look = recomendar(sem_casaco, ctx)[0]
    texto = explicacao.por_template(look, ctx)
    assert "pedem agasalho" not in texto and "vale levar um agasalho" in texto

    ameno = Contexto(formalidade_alvo=2, temperatura=19)
    assert "confortável" in explicacao.por_template(recomendar(sem_casaco, ameno)[0], ameno)


# ---------------------------------------------------- pesos e preferências
def test_ajustar_pesos_e_robusto():
    """Fase 2, itens 4 e 7."""
    padrao = normalizar_pesos(None)
    assert ajustar_pesos(padrao, {}, True) == {k: round(v, 4) for k, v in padrao.items()}
    assert ajustar_pesos(padrao, None, False) == ajustar_pesos(padrao, {"x": "y"}, True)
    assert pesos_validos(ajustar_pesos({"ocasiao": -1}, {"cor": 0.9, "clima": 0.2}, True))
    assert normalizar_pesos({"ocasiao": "a"}) == padrao
    assert not pesos_validos({**padrao, "ocasiao": 0.9})
    assert not pesos_validos({"ocasiao": 1.0}) and not pesos_validos("x")
    dobro = normalizar_pesos({k: v * 2 for k, v in padrao.items()})
    assert abs(sum(dobro.values()) - 1) < 1e-9


def test_um_voto_negativo_nao_zera_a_categoria():
    assert taxa_suavizada(0, 1) == 1 / 3 and taxa_suavizada(0, 0) == 0.5
    assert taxa_suavizada(9, 10) > taxa_suavizada(1, 1) > 0.5


# ---------------------------------------------------------- desempenho
def test_prefiltro_limita_o_produto_cartesiano():
    """Fase 3, item 4: 30 × 20 × 10 × 10 = 60 mil looks em Python puro."""
    cores = ["preto", "branco", "azul", "verde", "cinza", "bege", "vinho", "marinho",
             "vermelho", "grafite"]
    pecas = ([peca(f"s{i}", "camiseta", cores[i % 10]) for i in range(30)]
             + [peca(f"i{i}", "calca-jeans", cores[i % 10]) for i in range(20)]
             + [peca(f"c{i}", "tenis", cores[i % 10]) for i in range(10)]
             + [peca(f"j{i}", "jaqueta-jeans", cores[i % 10]) for i in range(10)])
    inicio = time.perf_counter()
    looks = recomendar(pecas, Contexto(formalidade_alvo=2, temperatura=15))
    duracao = time.perf_counter() - inicio
    assert len(looks) == 3 and TOP_N_POR_PAPEL == 12
    assert duracao < 2.0, f"recomendação levou {duracao:.2f} s"
    # as cores não representadas no topo não são cortadas pelo pré-filtro
    assert len({l.pecas["superior"].cor_nome for l in looks}) >= 2


def test_pontuar_mantem_score_entre_zero_e_um_com_estilo():
    look = recomendar(acervo(*BASE), Contexto(formalidade_alvo=2, temperatura=25))[0]
    ctx = Contexto(formalidade_alvo=2, temperatura=25, estilo="minimalista")
    assert 0 <= pontuar(look, ctx, normalizar_pesos(None)).score <= 1
