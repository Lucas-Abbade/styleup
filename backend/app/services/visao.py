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

Três decisões que afetam acurácia e tempo (RNF01 e RNF03):

* **Fundo branco.** O recorte do rembg é RGBA; convertido direto para RGB, o
  fundo vira preto. O FashionCLIP foi ajustado em fotos de catálogo, de fundo
  branco, então a peça é composta sobre branco antes de ir ao modelo.
* **Textos codificados uma vez.** As descrições das categorias e dos atributos
  não mudam entre requisições; seus vetores são calculados no aquecimento e
  reaproveitados. Cada foto custa uma passada do codificador de imagem, em vez
  de três passadas de imagem mais três de texto.
* **Ensemble de prompts.** Cada categoria é a média normalizada dos vetores dos
  seus prompts (como no artigo original do CLIP). Antes, todos os prompts de
  todas as categorias disputavam um único softmax, e uma categoria com dois
  prompts parecidos dividia a própria probabilidade.
"""

from __future__ import annotations

import base64
import functools
import io
import logging
import threading
import time

import numpy as np
from PIL import Image

from . import cor as servico_cor
from .taxonomia import ATRIBUTOS, CATEGORIAS, Categoria

log = logging.getLogger(__name__)

LADO_MAXIMO = 1024          # redimensiona antes de processar: acelera tudo
NITIDEZ_MINIMA = 40.0       # variância do laplaciano; abaixo disso a foto está borrada
AREA_MINIMA_PECA = 0.03     # a peça precisa ocupar ao menos 3% do quadro
LADO_RECORTE = 768          # lado maior do recorte devolvido para a interface
ESCALA_LOGITS = 100.0       # temperatura do CLIP (exp do logit_scale treinado)
CONFIANCA_MINIMA = 0.45     # abaixo disso a interface pede conferência
MARGEM_MINIMA = 0.15        # diferença entre a 1ª e a 2ª categoria

_estado = {"situacao": "frio", "detalhe": "", "segundos": None}
_trava_aquecimento = threading.Lock()


class FotoInvalida(Exception):
    """A imagem não serve para catalogação. A mensagem vai direto ao usuário."""


class VisaoIndisponivel(Exception):
    """As dependências de visão não estão instaladas ou o modelo não carregou."""


# --------------------------------------------------------------- 1. preparo
def carregar(dados: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(dados))
        img.load()
    except Exception as exc:                     # noqa: BLE001
        raise FotoInvalida("Arquivo de imagem inválido ou corrompido.") from exc

    # fotos de celular vêm deitadas, com a rotação só no EXIF
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:                            # noqa: BLE001 — EXIF quebrado não impede
        pass

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
    try:
        from rembg import new_session          # import tardio: só quando for usar
    except ImportError as exc:
        raise VisaoIndisponivel(
            "Dependências de visão ausentes. Instale requirements-visao.txt.") from exc
    return new_session("u2net")


def segmentar(img: Image.Image) -> tuple[Image.Image, np.ndarray]:
    """Remove o fundo. Devolve (imagem RGBA, máscara booleana da peça)."""
    sessao = _sessao_rembg()
    from rembg import remove

    recortada = remove(img, session=sessao)
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


def sobre_branco(recortada: Image.Image) -> Image.Image:
    """Compõe o recorte RGBA sobre fundo branco, como uma foto de catálogo."""
    fundo = Image.new("RGB", recortada.size, (255, 255, 255))
    fundo.paste(recortada, mask=recortada.split()[3])
    return fundo


def miolo(mascara: np.ndarray, borda: int = 3) -> np.ndarray:
    """Máscara sem a borda da peça.

    Os pixels do contorno misturam peça e fundo (halo do recorte) e puxam a cor
    predominante para o tom do fundo. Se a erosão apagar tudo — peça fina, como
    um cinto —, vale a máscara original.
    """
    m = mascara.copy()
    for _ in range(borda):
        reduzida = m.copy()
        reduzida[1:, :] &= m[:-1, :]
        reduzida[:-1, :] &= m[1:, :]
        reduzida[:, 1:] &= m[:, :-1]
        reduzida[:, :-1] &= m[:, 1:]
        m = reduzida
    return m if m.sum() >= 0.3 * mascara.sum() else mascara


def recorte_para_interface(recortada: Image.Image, mascara: np.ndarray) -> str:
    """Recorte da peça, sem fundo, como data URL WebP.

    É esta imagem que a interface guarda no Storage, não a foto original: o
    cartão do guarda-roupa fica com cara de catálogo e — mais importante — o
    que estava atrás da peça (o quarto, outras pessoas) nunca sai do aparelho
    para o armazenamento. É minimização de dados na prática.
    """
    linhas, colunas = np.where(mascara)
    margem = 8
    caixa = (max(int(colunas.min()) - margem, 0), max(int(linhas.min()) - margem, 0),
             min(int(colunas.max()) + 1 + margem, recortada.width),
             min(int(linhas.max()) + 1 + margem, recortada.height))
    img = recortada.crop(caixa)
    if max(img.size) > LADO_RECORTE:
        escala = LADO_RECORTE / max(img.size)
        img = img.resize((max(1, round(img.width * escala)),
                          max(1, round(img.height * escala))), Image.LANCZOS)
    saida = io.BytesIO()
    img.save(saida, format="WEBP", quality=82, method=4)
    return "data:image/webp;base64," + base64.b64encode(saida.getvalue()).decode("ascii")


# --------------------------------------------------------- 3. classificação
@functools.lru_cache(maxsize=1)
def _modelo_clip():
    """FashionCLIP quando disponível; CLIP genérico como alternativa.

    O FashionCLIP foi ajustado em catálogos de moda e acerta bem mais em peças de
    vestuário. Se o download falhar (rede da faculdade, por exemplo), o CLIP
    genérico mantém o sistema de pé com acurácia menor.
    """
    try:
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise VisaoIndisponivel(
            "Dependências de visão ausentes. Instale requirements-visao.txt.") from exc

    from ..config import config

    for nome in (config.modelo_clip, "openai/clip-vit-base-patch32"):
        try:
            modelo = CLIPModel.from_pretrained(nome).eval()
            processador = CLIPProcessor.from_pretrained(nome)
            log.info("Modelo de visão carregado: %s", nome)
            return modelo, processador
        except Exception as exc:                 # noqa: BLE001
            log.warning("Falha ao carregar %s: %s", nome, exc)
    raise VisaoIndisponivel("Nenhum modelo CLIP pôde ser carregado.")


def _como_matriz(saida) -> np.ndarray:
    """Tensor (ou saída com `pooler_output`, nas versões novas) -> array unitário."""
    tensor = saida if hasattr(saida, "norm") else saida.pooler_output
    tensor = tensor / tensor.norm(dim=-1, keepdim=True)
    return tensor.cpu().numpy().astype(np.float64)


def _embutir_textos(textos: list[str]) -> np.ndarray:
    """Vetores unitários dos textos, (N, D). Único ponto que roda o codificador de texto."""
    import torch

    modelo, processador = _modelo_clip()
    entradas = processador(text=textos, return_tensors="pt", padding=True, truncation=True)
    with torch.inference_mode():
        return _como_matriz(modelo.get_text_features(**entradas))


def _embutir_imagem(img: Image.Image) -> np.ndarray:
    """Vetor unitário da imagem, (D,). Único ponto que roda o codificador de imagem."""
    import torch

    modelo, processador = _modelo_clip()
    entradas = processador(images=img, return_tensors="pt")
    with torch.inference_mode():
        return _como_matriz(modelo.get_image_features(**entradas))[0]


def _media_unitaria(vetores: np.ndarray) -> np.ndarray:
    media = vetores.mean(axis=0)
    return media / np.linalg.norm(media)


@functools.lru_cache(maxsize=1)
def _vetores_de_texto() -> tuple[np.ndarray, dict[str, tuple[list[str], np.ndarray]]]:
    """Vetores das categorias e dos atributos, calculados uma única vez."""
    prompts: list[str] = []
    fatias: list[tuple[int, int]] = []
    for cat in CATEGORIAS:
        dela = list(cat.prompts or (f"a photo of {cat.chave.replace('-', ' ')}",))
        fatias.append((len(prompts), len(prompts) + len(dela)))
        prompts.extend(dela)

    inicio_atributos: dict[str, tuple[list[str], int, int]] = {}
    for atributo, opcoes in ATRIBUTOS.items():
        rotulos = list(opcoes)
        textos = [f"a photo of clothing, {frases[0]}" for frases in opcoes.values()]
        inicio_atributos[atributo] = (rotulos, len(prompts), len(prompts) + len(textos))
        prompts.extend(textos)

    vetores = _embutir_textos(prompts)
    categorias = np.stack([_media_unitaria(vetores[a:b]) for a, b in fatias])
    atributos = {nome: (rotulos, vetores[a:b])
                 for nome, (rotulos, a, b) in inicio_atributos.items()}
    return categorias, atributos


def _softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - logits.max())
    return e / e.sum()


def classificar_vetor(vetor: np.ndarray) -> tuple[Categoria, dict[str, float]]:
    """Categoria mais próxima do vetor da imagem, com as três melhores e suas notas."""
    categorias, _ = _vetores_de_texto()
    probs = _softmax(ESCALA_LOGITS * categorias @ vetor)
    ordem = probs.argsort()[::-1]
    confianca = {CATEGORIAS[i].chave: round(float(probs[i]), 4) for i in ordem[:3]}
    return CATEGORIAS[int(ordem[0])], confianca


def atributos_do_vetor(vetor: np.ndarray) -> dict[str, str]:
    """Manga e estampa, no mesmo esquema zero-shot, sem nova passada do modelo."""
    _, atributos = _vetores_de_texto()
    return {nome: rotulos[int((vetores @ vetor).argmax())]
            for nome, (rotulos, vetores) in atributos.items()}


def classificar(img: Image.Image) -> tuple[Categoria, dict[str, float]]:
    """Escolhe a categoria da taxonomia mais próxima da imagem."""
    return classificar_vetor(_embutir_imagem(img))


def atributos(img: Image.Image) -> dict[str, str]:
    return atributos_do_vetor(_embutir_imagem(img))


def confianca_baixa(confianca: dict[str, float]) -> bool:
    """A interface destaca o seletor de categoria quando o modelo hesitou."""
    notas = sorted(confianca.values(), reverse=True)
    if not notas:
        return True
    segunda = notas[1] if len(notas) > 1 else 0.0
    return notas[0] < CONFIANCA_MINIMA or notas[0] - segunda < MARGEM_MINIMA


# ------------------------------------------------------------ 4. aquecimento
def estado() -> dict:
    """Situação dos modelos, exposta em /saude: frio, aquecendo, pronto, indisponivel."""
    return dict(_estado)


def aquecer() -> None:
    """Carrega rembg e CLIP e codifica os textos, antes da primeira foto.

    Sem isto, a primeira análise do dia pagava o carregamento (e, na primeira
    vez, o download: 128 s medidos). Roda em thread própria na subida da API,
    então /saude responde enquanto os modelos carregam.
    """
    with _trava_aquecimento:
        if _estado["situacao"] == "pronto":
            return
        _estado.update(situacao="aquecendo", detalhe="")
        inicio = time.perf_counter()
        try:
            _sessao_rembg()
            _vetores_de_texto()
            # uma passada com imagem sintética: aloca buffers e compila o grafo
            _embutir_imagem(Image.new("RGB", (224, 224), (128, 128, 128)))
        except VisaoIndisponivel as exc:
            _estado.update(situacao="indisponivel", detalhe=str(exc))
            log.info("Visão indisponível: %s", exc)
            return
        except Exception as exc:                 # noqa: BLE001
            _estado.update(situacao="indisponivel", detalhe=str(exc))
            log.warning("Falha ao aquecer os modelos de visão: %s", exc)
            return
        _estado.update(situacao="pronto", segundos=round(time.perf_counter() - inicio, 1))
        log.info("Modelos de visão prontos em %.1f s", _estado["segundos"])


# ------------------------------------------------------------ 5. orquestração
def analisar(dados: bytes, com_recorte: bool = True) -> dict:
    """Pipeline completo. Devolve tudo o que a tela de confirmação precisa.

    Nada aqui é gravado: o usuário confirma ou corrige antes de virar peça, que é
    o que a operação 6.2.2 do Documento de Visão descreve.
    """
    img = carregar(dados)
    validar(img)

    recortada, mascara = segmentar(img)
    rgb = np.asarray(recortada)[:, :, :3]
    pixels = rgb[miolo(mascara)]

    vetor = _embutir_imagem(sobre_branco(recortada))
    categoria, confianca = classificar_vetor(vetor)
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
        "atributos": atributos_do_vetor(vetor),
        "cor_nome": nome_cor,
        "cor_hex": servico_cor.hsv_para_hex(h, s, v),
        "cor_hsv": [round(h, 2), round(s, 4), round(v, 4)],
        "neutra": neutra,
        "confianca": confianca,
        "confianca_baixa": confianca_baixa(confianca),
        "recorte": recorte_para_interface(recortada, mascara) if com_recorte else None,
    }
