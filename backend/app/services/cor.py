"""Extração e nomeação da cor predominante de uma peça.

Duas responsabilidades separadas de propósito:

1. `cor_predominante` — recebe os pixels da peça já recortada (fundo removido) e
   devolve o centroide dominante em HSV, via k-means. É o que a seção 5.1 do
   Documento de Visão chama de "extração da cor predominante".

2. `nomear` — traduz esse HSV para um nome em português. Esta parte não é
   cosmética: o RNF05 exige que a cor apareça em texto, porque um usuário com
   daltonismo não consegue conferir a amostra visual.
"""

from __future__ import annotations

import colorsys

import numpy as np

# ------------------------------------------------------------------- nomes
# Faixas de matiz (graus). A ordem importa: a primeira faixa que contém o matiz
# vence, e o vermelho aparece duas vezes por atravessar o zero.
FAIXAS_MATIZ: tuple[tuple[float, float, str], ...] = (
    (0, 12, "vermelho"),
    (12, 40, "laranja"),
    (40, 68, "amarelo"),
    (68, 160, "verde"),
    (160, 200, "ciano"),
    (200, 250, "azul"),
    (250, 290, "roxo"),
    (290, 335, "rosa"),
    (335, 360, "vermelho"),
)

# Cores neutras combinam com quase tudo e recebem tratamento próprio no score.
NEUTRAS = {"preto", "branco", "cinza", "bege", "marinho"}

# Concordância de gênero. As ausentes são invariáveis em português
# ("calça azul", "camisa verde", "bota bege").
FEMININO = {
    "preto": "preta", "branco": "branca", "amarelo": "amarela",
    "vermelho": "vermelha", "roxo": "roxa", "marrom": "marrom",
}


def concordar(nome: str, genero: str) -> str:
    """Flexiona o nome da cor para acompanhar a peça: "camisa branca", "tênis branco"."""
    return FEMININO.get(nome, nome) if genero == "f" else nome


def rgb_para_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """RGB 0-255 -> HSV com matiz em graus e saturação/valor em 0-1."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v


def hsv_para_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, s, v)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def nomear(h: float, s: float, v: float) -> tuple[str, bool]:
    """Devolve (nome em português, é neutra).

    A ordem dos testes reflete como a percepção funciona: primeiro decidimos se
    a cor tem matiz relevante; só então perguntamos qual matiz é.
    """
    if v < 0.12:
        return "preto", True
    if s < 0.12:
        if v > 0.88:
            return "branco", True
        return "cinza", True
    if s < 0.30 and 20 <= h <= 55 and v > 0.45:
        return "bege", True
    # azul muito escuro é lido como marinho, e funciona como neutro no vestuário
    if 200 <= h <= 250 and v < 0.42:
        return "marinho", True

    for inicio, fim, nome in FAIXAS_MATIZ:
        if inicio <= h < fim:
            if nome == "laranja" and v < 0.45:
                return "marrom", True
            if nome == "vermelho" and v < 0.40:
                return "vinho", False
            return nome, nome in NEUTRAS
    return "indefinida", False


def cor_predominante(
    pixels: np.ndarray,
    k: int = 4,
    iteracoes: int = 25,
    semente: int = 0,
) -> tuple[float, float, float]:
    """k-means sobre os pixels da peça; devolve o centroide mais populoso em HSV.

    `pixels` é um array (N, 3) em RGB 0-255, já sem os pixels de fundo. Rodamos o
    k-means no espaço RGB (onde a distância euclidiana faz sentido) e convertemos
    só o vencedor para HSV — converter antes distorceria a distância, porque o
    matiz é circular.
    """
    if pixels.size == 0:
        raise ValueError("nenhum pixel de peça: a segmentação removeu a imagem inteira")

    dados = np.asarray(pixels, dtype=np.float64).reshape(-1, 3)
    if len(dados) > 20_000:                       # amostragem: acurácia igual, muito mais rápido
        rng = np.random.default_rng(semente)
        dados = dados[rng.choice(len(dados), 20_000, replace=False)]

    k = min(k, len(dados))
    rng = np.random.default_rng(semente)
    centros = dados[rng.choice(len(dados), k, replace=False)].copy()

    rotulos = np.zeros(len(dados), dtype=int)
    for _ in range(iteracoes):
        dist = ((dados[:, None, :] - centros[None, :, :]) ** 2).sum(axis=2)
        novos = dist.argmin(axis=1)
        if np.array_equal(novos, rotulos):
            break
        rotulos = novos
        for i in range(k):
            membros = dados[rotulos == i]
            if len(membros):
                centros[i] = membros.mean(axis=0)

    contagem = np.bincount(rotulos, minlength=k)
    r, g, b = centros[int(contagem.argmax())]
    return rgb_para_hsv(int(r), int(g), int(b))


# --------------------------------------------------------------- harmonia
def distancia_matiz(h1: float, h2: float) -> float:
    """Menor distância angular entre dois matizes, em graus (0 a 180)."""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def harmonia(cor_a: tuple[float, float, float], neutra_a: bool,
             cor_b: tuple[float, float, float], neutra_b: bool) -> float:
    """Nota de 0 a 1 para a combinação de duas cores.

    Baseado nos esquemas clássicos de Itten (referência 1.4 do documento):
    neutro combina com tudo; matizes iguais ou análogos combinam; complementares
    combinam com ressalva; o intervalo intermediário é o que costuma destoar.
    """
    if neutra_a and neutra_b:
        return 0.90                       # elegante, porém sem contraste
    if neutra_a or neutra_b:
        return 1.00                       # neutro + cor é a aposta mais segura
    d = distancia_matiz(cor_a[0], cor_b[0])
    if d <= 20:
        return 0.85                       # monocromático
    if d <= 60:
        return 0.80                       # análogo
    if d >= 150:
        return 0.70                       # complementar: funciona, mas chama atenção
    if 100 <= d < 150:
        return 0.45                       # tríade imperfeita
    return 0.35                           # zona de conflito
