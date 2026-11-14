"""Extração e nomeação da cor predominante de uma peça.

Duas responsabilidades separadas de propósito:

1. `cor_predominante` — recebe os pixels da peça já recortada (fundo removido) e
   devolve o centroide dominante em HSV, via k-means. É o que a seção 5.1 do
   Documento de Visão chama de "extração da cor predominante".

2. `nomear` — traduz esse HSV para um nome em português. Esta parte não é
   cosmética: o RNF05 exige que a cor apareça em texto, porque um usuário com
   daltonismo não consegue conferir a amostra visual.

3. `harmonia` — nota de combinação entre duas cores, usada pelo recomendador.
"""

from __future__ import annotations

import colorsys
import math
import re
from functools import lru_cache

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
NEUTRAS = {"preto", "grafite", "cinza", "branco", "bege", "cáqui", "marrom", "marinho"}

# Famílias usadas pelas diretrizes de estilo ("tons terrosos", "all black").
TERROSAS = {"marrom", "bege", "cáqui", "caramelo", "verde-oliva", "mostarda", "vinho"}

# Todos os nomes que `nomear` pode devolver — a interface usa para o seletor.
NOMES_CONHECIDOS: tuple[str, ...] = (
    "preto", "grafite", "cinza", "branco", "bege", "cáqui", "marrom", "caramelo",
    "marinho", "azul", "azul-claro", "ciano", "verde", "verde-oliva", "amarelo",
    "mostarda", "laranja", "vermelho", "vinho", "rosa", "roxo",
)

# Cor de referência de cada nome: é o que a tela de edição grava quando o
# usuário corrige a cor escolhendo pelo nome.
HEX_REFERENCIA: dict[str, str] = {
    "preto": "#1a1a1a", "grafite": "#3d3d40", "cinza": "#8c8c8c", "branco": "#f4f4f2",
    "bege": "#d9c6a3", "cáqui": "#b09a6b", "marrom": "#6b4423", "caramelo": "#b5651d",
    "marinho": "#1c2a4a", "azul": "#2f5fb3", "azul-claro": "#9cc3e6",
    "ciano": "#2aa5a5", "verde": "#2e8b47", "verde-oliva": "#6b7340",
    "amarelo": "#f0c828", "mostarda": "#c99a1e", "laranja": "#eb8c28",
    "vermelho": "#d42a2a", "vinho": "#6e1f2b", "rosa": "#e58fb1", "roxo": "#6f3fa0",
}

# Concordância de gênero. As ausentes são invariáveis em português
# ("calça azul", "camisa verde", "bota bege", "camisa vinho").
FEMININO = {
    "preto": "preta", "branco": "branca", "amarelo": "amarela",
    "vermelho": "vermelha", "roxo": "roxa", "marrom": "marrom",
    "azul-claro": "azul-clara",
}

_HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def concordar(nome: str, genero: str) -> str:
    """Flexiona o nome da cor para acompanhar a peça: "camisa branca", "tênis branco"."""
    return FEMININO.get(nome, nome) if genero == "f" else nome


def rgb_para_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """RGB 0-255 -> HSV com matiz em graus e saturação/valor em 0-1."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v


def hsv_para_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, s, v)
    return round(r * 255), round(g * 255), round(b * 255)


def hsv_para_hex(h: float, s: float, v: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(*hsv_para_rgb(h, s, v))


def hex_valido(valor: str) -> bool:
    return bool(_HEX.match(valor or ""))


def hex_para_hsv(valor: str) -> tuple[float, float, float]:
    """'#1c2a4a' -> HSV. É o que mantém `cor_hsv` coerente quando o usuário
    corrige a cor: a harmonia do recomendador lê o HSV, não o nome."""
    m = _HEX.match(valor or "")
    if not m:
        raise ValueError(f"cor hexadecimal inválida: {valor!r}")
    n = int(m.group(1), 16)
    return rgb_para_hsv(n >> 16, (n >> 8) & 0xFF, n & 0xFF)


@lru_cache(maxsize=4096)
def luminosidade(h: float, s: float, v: float) -> float:
    """L* do CIELAB (0 preto, 100 branco): claridade como o olho percebe.

    O V do HSV engana — amarelo e azul puros têm o mesmo V e claridades muito
    diferentes —, e é o contraste de claridade que separa visualmente as peças.
    """
    def linear(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = hsv_para_rgb(h, s, v)
    y = 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
    return 116 * y ** (1 / 3) - 16 if y > 0.008856 else 903.3 * y


def nomear(h: float, s: float, v: float) -> tuple[str, bool]:
    """Devolve (nome em português, é neutra).

    A ordem dos testes reflete como a percepção funciona: primeiro decidimos se
    a cor tem matiz relevante; só então perguntamos qual matiz é.
    """
    h = h % 360
    if v < 0.12:
        return "preto", True
    if s < 0.12:
        if v > 0.88:
            return "branco", True
        if v < 0.32:
            return "grafite", True
        return "cinza", True
    if s < 0.30 and 20 <= h <= 55 and v > 0.45:
        return "bege", True
    # azul muito escuro é lido como marinho, e funciona como neutro no vestuário
    if 200 <= h <= 250 and v < 0.42:
        return "marinho", True
    if 190 <= h <= 250 and s < 0.45 and v > 0.70:
        return "azul-claro", False
    # verdes amarelados e pouco saturados: o "verde-oliva" / militar do vestuário
    if 50 <= h <= 100 and s < 0.62 and 0.20 <= v <= 0.62:
        return "verde-oliva", False
    if 30 <= h <= 60 and 0.25 <= s < 0.55 and 0.45 <= v <= 0.78:
        return "cáqui", True

    for inicio, fim, nome in FAIXAS_MATIZ:
        if inicio <= h < fim:
            if nome == "laranja":
                if v < 0.45:
                    return "marrom", True
                if v < 0.75 and s > 0.45:
                    return "caramelo", False
            if nome == "amarelo" and v <= 0.85 and s > 0.55:
                return "mostarda", False
            if nome == "vermelho" and v < 0.45:
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
    return rgb_para_hsv(round(r), round(g), round(b))


# --------------------------------------------------------------- harmonia
def distancia_matiz(h1: float, h2: float) -> float:
    """Menor distância angular entre dois matizes, em graus (0 a 180)."""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def _rampa(valor: float, inicio: float, fim: float) -> float:
    """0 abaixo de `inicio`, 1 acima de `fim`, linear no meio."""
    if valor <= inicio:
        return 0.0
    if valor >= fim:
        return 1.0
    return (valor - inicio) / (fim - inicio)


def _nota_matiz(d: float) -> float:
    """Harmonia cai com a diferença de matiz e não se recupera nos complementares.

    Schloss & Palmer (2011) mediram isso com participantes: a harmonia percebida
    é máxima em matizes iguais e decresce com a distância, sem alta confiável nos
    opostos. O degrau "complementar = 0,70" da versão anterior era convenção de
    círculo cromático, não resultado medido.
    """
    if d <= 20:
        return 0.88
    if d <= 60:
        return 0.88 - 0.10 * (d - 20) / 40          # análogos: 0,88 -> 0,78
    if d <= 120:
        return 0.78 - 0.36 * (d - 60) / 60          # zona de conflito: 0,78 -> 0,42
    return 0.42


@lru_cache(maxsize=65536)
def harmonia(cor_a: tuple[float, float, float], neutra_a: bool,
             cor_b: tuple[float, float, float], neutra_b: bool) -> float:
    """Nota de 0 a 1 para a combinação de duas cores.

    Três fatores, na ordem em que a literatura os sustenta (Ou & Luo 2006;
    Schloss & Palmer 2011; O'Donovan et al. 2011):

    * neutro combina com tudo — é a regra de vestuário mais consensual;
    * entre duas cores, quanto mais próximos os matizes, melhor; e duas cores
      vivas brigam mais do que duas apagadas (o croma pondera o conflito);
    * contraste de claridade ajuda: a faixa útil vai de ΔL* ≈ 5 a ≈ 20.
    """
    contraste = _rampa(abs(luminosidade(*cor_a) - luminosidade(*cor_b)), 5, 20)

    if neutra_a and neutra_b:
        # preto com preto é intenção; preto com grafite parece engano
        iguais = (distancia_matiz(cor_a[0], cor_b[0]) < 15
                  and abs(cor_a[1] - cor_b[1]) < 0.1 and abs(cor_a[2] - cor_b[2]) < 0.06)
        return 0.88 if iguais else round(0.82 + 0.13 * contraste, 4)
    if neutra_a or neutra_b:
        return round(0.90 + 0.10 * contraste, 4)

    base = _nota_matiz(distancia_matiz(cor_a[0], cor_b[0]))
    croma = math.sqrt(max(cor_a[1] * cor_a[2], 0) * max(cor_b[1] * cor_b[2], 0))
    intensidade = min(1.0, max(0.35, croma / 0.45))
    nota = 1 - (1 - base) * intensidade + 0.05 * contraste
    return round(min(0.95, nota), 4)
