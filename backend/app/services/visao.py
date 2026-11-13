"""Serviço de visão computacional (módulos M1 e M2), abordagem zero-shot.

Decisão de projeto: **não treinamos modelo**. O pipeline é

    foto -> validação -> remoção de fundo (rembg/U²-Net) -> classificação
    zero-shot (FashionCLIP) -> extração de cor (k-means sobre a máscara)

A classificação zero-shot compara a imagem com descrições textuais das
categorias da taxonomia. Trocar uma categoria é editar `taxonomia.py`, sem
retreino e sem rotular nada — que é exatamente o motivo de caber num prazo de
um mês.

Os modelos são carregados sob demanda e mantidos em cache de processo. O import
deste módulo não puxa torch, então o resto do time roda a API sem instalar 2 GB
de dependências.
"""

from __future__ import annotations

import functools
import io
import logging

import numpy as np
from PIL import Image

from . import cor as servico_cor
from .taxonomia import ATRIBUTOS, CATEGORIAS, Categoria

log = logging.getLogger(__name__)

LADO_MAXIMO = 1024          # redimensiona antes de processar: acelera tudo
NITIDEZ_MINIMA = 40.0       # variância do laplaciano; abaixo disso a foto está borrada
AREA_MINIMA_PECA = 0.03     # a peça precisa ocupar ao menos 3% do quadro


class FotoInvalida(Exception):
    """A imagem não serve para catalogação. A mensagem vai direto ao usuário."""


# --------------------------------------------------------------- 1. preparo
def carregar(dados: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(dados))
        img.load()
    except Exception as exc:                     # noqa: BLE001
        raise FotoInvalida("Arquivo de imagem inválido ou corrompido.") from exc

    img = img.convert("RGB")
    if max(img.size) > LADO_MAXIMO:
        escala = LADO_MAXIMO / max(img.size)
        img = img.resize((round(img.width * escala), round(img.height * escala)),
                         Image.LANCZOS)
    return img


def nitidez(img: Image.Image) -> float:
    """Variância do laplaciano em escala de cinza. Métrica clássica de foco."""
    cinza = np.asarray(img.convert("L"), dtype=np.float64)
    nucleo = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
    h, w = cinza.shape
    if h < 3 or w < 3:
        return 0.0
    janelas = np.lib.stride_tricks.sliding_window_view(cinza, (3, 3))
    return float((janelas * nucleo).sum(axis=(2, 3)).var())


def validar(img: Image.Image) -> None:
    if min(img.size) < 128:
        raise FotoInvalida("A foto está pequena demais. Aproxime a peça e tente de novo.")
    if nitidez(img) < NITIDEZ_MINIMA:
        raise FotoInvalida("A foto parece borrada. Firme a câmera e tente de novo.")


# ---------------------------------------------------------- 2. segmentação
@functools.lru_cache(maxsize=1)
def _sessao_rembg():
    from rembg import new_session          # import tardio: só quando for usar
    return new_session("u2net")


def segmentar(img: Image.Image) -> tuple[Image.Image, np.ndarray]:
    """Remove o fundo. Devolve (imagem RGBA, máscara booleana da peça)."""
    from rembg import remove

    recortada = remove(img, session=_sessao_rembg())
    if recortada.mode != "RGBA":
        recortada = recortada.convert("RGBA")

    alfa = np.asarray(recortada)[:, :, 3]
    mascara = alfa > 128

    proporcao = mascara.mean()
    if proporcao < AREA_MINIMA_PECA:
        raise FotoInvalida(
            "Não foi possível isolar a peça. Fotografe sobre um fundo liso, "
            "com a peça ocupando a maior parte do quadro."
        )
    return recortada, mascara


# --------------------------------------------------------- 3. classificação
@functools.lru_cache(maxsize=1)
def _modelo_clip():
    """FashionCLIP quando disponível; CLIP genérico como alternativa.

    O FashionCLIP foi ajustado em catálogos de moda e acerta bem mais em peças de
    vestuário. Se o download falhar (rede da faculdade, por exemplo), o CLIP
    genérico mantém o sistema de pé com acurácia menor.
    """
    from transformers import CLIPModel, CLIPProcessor

    from ..config import config

    for nome in (config.modelo_clip, "openai/clip-vit-base-patch32"):
        try:
            modelo = CLIPModel.from_pretrained(nome).eval()
            processador = CLIPProcessor.from_pretrained(nome)
            log.info("Modelo de visão carregado: %s", nome)
            return modelo, processador
        except Exception as exc:                 # noqa: BLE001
            log.warning("Falha ao carregar %s: %s", nome, exc)
    raise RuntimeError("Nenhum modelo CLIP pôde ser carregado.")


def _similaridades(img: Image.Image, textos: list[str]) -> np.ndarray:
    import torch

    modelo, processador = _modelo_clip()
    entradas = processador(text=textos, images=img, return_tensors="pt",
                           padding=True, truncation=True)
    with torch.no_grad():
        saida = modelo(**entradas)
    return saida.logits_per_image.softmax(dim=1).numpy()[0]


def classificar(img: Image.Image) -> tuple[Categoria, dict[str, float]]:
    """Escolhe a categoria da taxonomia mais próxima da imagem.

    Cada categoria tem vários prompts; usamos o melhor de cada uma, porque uma
    descrição infeliz não deve enterrar a categoria certa.
    """
    prompts: list[str] = []
    indices: list[int] = []
    for i, cat in enumerate(CATEGORIAS):
        for p in (cat.prompts or (f"a photo of {cat.chave.replace('-', ' ')}",)):
            prompts.append(p)
            indices.append(i)

    probs = _similaridades(img, prompts)
    por_categoria = np.zeros(len(CATEGORIAS))
    for prob, idx in zip(probs, indices):
        por_categoria[idx] = max(por_categoria[idx], prob)

    melhor = int(por_categoria.argmax())
    confianca = {
        CATEGORIAS[i].chave: round(float(por_categoria[i]), 4)
        for i in por_categoria.argsort()[-3:][::-1]
    }
    return CATEGORIAS[melhor], confianca


def atributos(img: Image.Image) -> dict[str, str]:
    """Manga e estampa, no mesmo esquema zero-shot."""
    resultado: dict[str, str] = {}
    for atributo, opcoes in ATRIBUTOS.items():
        rotulos = list(opcoes.keys())
        textos = [f"a photo of clothing, {frases[0]}" for frases in opcoes.values()]
        probs = _similaridades(img, textos)
        resultado[atributo] = rotulos[int(probs.argmax())]
    return resultado


# ------------------------------------------------------------ 4. orquestração
def analisar(dados: bytes) -> dict:
    """Pipeline completo. Devolve tudo o que a tela de confirmação precisa.

    Nada aqui é gravado: o usuário confirma ou corrige antes de virar peça, que é
    o que a operação 6.2.2 do Documento de Visão descreve.
    """
    img = carregar(dados)
    validar(img)

    recortada, mascara = segmentar(img)
    rgb = np.asarray(recortada)[:, :, :3]
    pixels = rgb[mascara]

    categoria, confianca = classificar(recortada)
    h, s, v = servico_cor.cor_predominante(pixels)
    nome_cor, neutra = servico_cor.nomear(h, s, v)

    return {
        "categoria": categoria.chave,
        "rotulo": categoria.rotulo,
        "papel": categoria.papel,
        "formalidade": categoria.formalidade,
        "temp_min": categoria.temp_min,
        "temp_max": categoria.temp_max,
        "resiste_chuva": categoria.resiste_chuva,
        "atributos": atributos(recortada),
        "cor_nome": nome_cor,
        "cor_hex": servico_cor.hsv_para_hex(h, s, v),
        "cor_hsv": [round(h, 2), round(s, 4), round(v, 4)],
        "neutra": neutra,
        "confianca": confianca,
    }
