"""Partes do pipeline de visão que não dependem de torch nem de download.

O modelo em si (FashionCLIP) não roda nos testes: os dois pontos que o chamam
são substituídos por vetores sintéticos. O que se testa aqui é a lógica em
volta — a que decide a categoria a partir dos vetores, compõe o fundo branco,
recorta a peça e extrai a cor. A acurácia real se mede com
`scripts/medir_acuracia.py`, em fotos rotuladas.
"""

from __future__ import annotations

import base64
import io

import numpy as np
import pytest
from PIL import Image

from app.services import visao
from app.services.taxonomia import ATRIBUTOS, CATEGORIAS


@pytest.fixture
def modelo_falso(monkeypatch):
    """Cada texto vira um vetor one-hot; a imagem é a soma dos textos escolhidos."""
    chamadas = {"texto": 0, "imagem": 0}
    visao._vetores_de_texto.cache_clear()

    def textos(lista):
        chamadas["texto"] += 1
        chamadas["dim"] = len(lista)
        return np.eye(len(lista))

    monkeypatch.setattr(visao, "_embutir_textos", textos)
    yield chamadas
    visao._vetores_de_texto.cache_clear()


def _vetor_para(chave: str, dim: int, extra: dict[int, float] | None = None) -> np.ndarray:
    """Vetor de imagem alinhado com TODOS os prompts da categoria `chave`."""
    v = np.zeros(dim)
    posicao = 0
    for cat in CATEGORIAS:
        n = len(cat.prompts or (1,))
        if cat.chave == chave:
            v[posicao:posicao + n] = 1.0
        posicao += n
    for i, peso in (extra or {}).items():
        v[i] = peso
    return v / np.linalg.norm(v)


def test_classifica_pela_media_dos_prompts_e_devolve_top3(modelo_falso):
    visao._vetores_de_texto()
    dim = modelo_falso["dim"]
    for chave in ("camiseta", "calca-jeans", "bone", "blazer"):
        categoria, confianca = visao.classificar_vetor(_vetor_para(chave, dim))
        assert categoria.chave == chave
        assert len(confianca) == 3 and list(confianca)[0] == chave
        assert not visao.confianca_baixa(confianca)


def test_textos_sao_codificados_uma_unica_vez(modelo_falso):
    """Fase 3: antes, cada foto rodava o codificador de texto três vezes."""
    visao._vetores_de_texto()
    dim = modelo_falso["dim"]
    for _ in range(5):
        visao.classificar_vetor(_vetor_para("tenis", dim))
        visao.atributos_do_vetor(_vetor_para("tenis", dim))
    assert modelo_falso["texto"] == 1


def test_atributos_saem_do_mesmo_vetor(modelo_falso):
    visao._vetores_de_texto()
    dim = modelo_falso["dim"]
    total_categorias = sum(len(c.prompts or (1,)) for c in CATEGORIAS)
    # manga: [curta, longa] · estampa: [lisa, listrada, estampada, xadrez]
    v = _vetor_para("camiseta", dim, {total_categorias + 1: 0.9, total_categorias + 2 + 3: 0.9})
    assert visao.atributos_do_vetor(v) == {"manga": "longa", "estampa": "xadrez"}
    assert set(visao.atributos_do_vetor(v)) == set(ATRIBUTOS)


def test_confianca_baixa_quando_o_modelo_hesita():
    assert visao.confianca_baixa({"polo": 0.40, "camiseta": 0.35, "regata": 0.1})
    assert visao.confianca_baixa({"polo": 0.55, "camiseta": 0.45})
    assert not visao.confianca_baixa({"polo": 0.80, "camiseta": 0.10})
    assert visao.confianca_baixa({})


def _recorte_vermelho():
    """Quadrado vermelho opaco no meio de uma imagem transparente."""
    rgba = np.zeros((200, 300, 4), dtype=np.uint8)
    rgba[50:150, 100:220] = (200, 30, 30, 255)
    return Image.fromarray(rgba, "RGBA"), rgba[:, :, 3] > 128


def test_peca_vai_ao_modelo_sobre_fundo_branco():
    """O recorte RGBA convertido direto para RGB ficava com fundo PRETO; o
    FashionCLIP foi ajustado em fotos de catálogo, de fundo branco."""
    recortada, _ = _recorte_vermelho()
    composta = visao.sobre_branco(recortada)
    assert composta.mode == "RGB"
    assert composta.getpixel((5, 5)) == (255, 255, 255)
    assert composta.getpixel((150, 100)) == (200, 30, 30)
    assert recortada.convert("RGB").getpixel((5, 5)) == (0, 0, 0)      # o defeito antigo


def test_miolo_descarta_a_borda_e_preserva_pecas_finas():
    _, mascara = _recorte_vermelho()
    dentro = visao.miolo(mascara, borda=3)
    assert dentro.sum() < mascara.sum() and dentro[100, 160] and not dentro[50, 100]
    fina = np.zeros((50, 200), dtype=bool)
    fina[24:27, 10:190] = True                       # um cinto: 3 px de altura
    assert visao.miolo(fina).sum() == fina.sum()


def test_recorte_para_a_interface_e_webp_transparente_e_ajustado():
    recortada, mascara = _recorte_vermelho()
    url = visao.recorte_para_interface(recortada, mascara)
    assert url.startswith("data:image/webp;base64,")
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert img.mode == "RGBA" and img.size == (136, 116)     # peça + 8 px de margem
    assert img.getpixel((2, 2))[3] == 0 and img.getpixel((68, 58))[3] == 255
    assert len(url) < 5000


def test_validacao_da_foto():
    with pytest.raises(visao.FotoInvalida, match="inválido"):
        visao.carregar(b"isto nao e uma imagem")
    pequena = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(pequena, "PNG")
    with pytest.raises(visao.FotoInvalida, match="pequena"):
        visao.validar(visao.carregar(pequena.getvalue()))
    with pytest.raises(visao.FotoInvalida, match="borrada"):
        visao.validar(Image.new("RGB", (400, 400), "gray"))
    ruido = Image.fromarray(np.random.default_rng(0).integers(0, 255, (300, 300, 3), dtype=np.uint8))
    visao.validar(ruido)


def test_foto_grande_e_reduzida_e_respeita_a_orientacao_exif():
    deitada = Image.new("RGB", (3000, 2000), "white")
    exif = deitada.getexif()
    exif[0x0112] = 6                                  # girar 90° para exibir
    saida = io.BytesIO()
    deitada.save(saida, "JPEG", exif=exif)
    img = visao.carregar(saida.getvalue())
    assert max(img.size) == visao.LADO_MAXIMO and img.height > img.width


def test_analise_completa_com_modelos_simulados(modelo_falso, monkeypatch):
    recortada, mascara = _recorte_vermelho()
    monkeypatch.setattr(visao, "validar", lambda img: None)
    monkeypatch.setattr(visao, "segmentar", lambda img: (recortada, mascara))
    visao._vetores_de_texto()
    vistos = []

    def imagem(img):
        vistos.append(img)
        return _vetor_para("polo", modelo_falso["dim"])
    monkeypatch.setattr(visao, "_embutir_imagem", imagem)

    foto = io.BytesIO()
    Image.new("RGB", (300, 200), "white").save(foto, "PNG")
    r = visao.analisar(foto.getvalue())
    assert (r["categoria"], r["papel"], r["rotulo"]) == ("polo", "superior", "Camisa polo")
    assert r["cor_nome"] == "vermelho" and r["cor_hex"] == "#c81e1e" and r["neutra"] is False
    assert len(r["cor_hsv"]) == 3 and r["recorte"].startswith("data:image/webp")
    assert len(vistos) == 1 and vistos[0].getpixel((0, 0)) == (255, 255, 255)
    assert visao.analisar(foto.getvalue(), com_recorte=False)["recorte"] is None


def test_aquecimento_sem_dependencias_marca_indisponivel(monkeypatch):
    def faltando():
        raise visao.VisaoIndisponivel("Dependências de visão ausentes.")
    monkeypatch.setattr(visao, "_sessao_rembg", faltando)
    monkeypatch.setitem(visao._estado, "situacao", "frio")
    visao.aquecer()
    assert visao.estado()["situacao"] == "indisponivel"
