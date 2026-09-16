"""Rotas de catalogação e do guarda-roupa digital (seções 6.2 e 6.3)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..db import obter_repositorio
from ..repositorio import Repositorio
from ..schemas import AnaliseFoto, PecaAtualizacao, PecaEntrada, PecaSaida
from ..services import visao
from ..services.taxonomia import CATEGORIAS, POR_CHAVE

log = logging.getLogger(__name__)
# O Starlette renomeou HTTP_422_UNPROCESSABLE_ENTITY; o numero e estavel.
HTTP_422 = 422

router = APIRouter(prefix="/pecas", tags=["peças"])

TAMANHO_MAXIMO = 12 * 1024 * 1024      # 12 MB: foto de celular cabe com folga
TIPOS_ACEITOS = ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif")


@router.get("/taxonomia")
def taxonomia():
    """Catálogo de categorias conhecidas. A interface usa no seletor manual."""
    return [
        {
            "chave": c.chave, "rotulo": c.rotulo, "papel": c.papel,
            "formalidade": c.formalidade, "temp_min": c.temp_min,
            "temp_max": c.temp_max, "resiste_chuva": c.resiste_chuva,
        }
        for c in CATEGORIAS
    ]


@router.post("/analisar", response_model=AnaliseFoto)
async def analisar(foto: UploadFile = File(...)):
    """6.2.1 — análise automática da fotografia.

    Não grava nada: devolve a sugestão para o usuário confirmar ou corrigir.
    """
    if foto.content_type and not foto.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "Envie um arquivo de imagem.")

    dados = await foto.read()
    if not dados:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio.")
    if len(dados) > TAMANHO_MAXIMO:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            "Foto maior que 12 MB.")

    try:
        return visao.analisar(dados)
    except visao.FotoInvalida as exc:
        # 422 com mensagem em português: o texto vai direto para a tela
        raise HTTPException(HTTP_422, str(exc))
    except Exception as exc:                         # noqa: BLE001
        # qualquer falha inesperada do pipeline vira erro tratado, nunca 500 cru
        log.exception("Falha inesperada ao analisar a foto")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "O serviço de análise de imagem está indisponível. Cadastre a peça "
            "manualmente ou tente novamente.",
        ) from exc


@router.post("", response_model=PecaSaida, status_code=status.HTTP_201_CREATED)
def registrar(entrada: PecaEntrada, repo: Repositorio = Depends(obter_repositorio)):
    """6.2.2 — registro da peça com identificador único."""
    if entrada.categoria not in POR_CHAVE:
        raise HTTPException(HTTP_422,
                            f"Categoria desconhecida: {entrada.categoria}")
    return repo.criar_peca(entrada.model_dump())


@router.get("", response_model=list[PecaSaida])
def listar(
    papel: str | None = None,
    categoria: str | None = None,
    cor: str | None = None,
    disponivel: bool | None = None,
    repo: Repositorio = Depends(obter_repositorio),
):
    """6.3.1 — consulta e filtro do guarda-roupa."""
    return repo.listar_pecas(
        papel=papel, categoria=categoria, cor_nome=cor, disponivel=disponivel)


@router.get("/resumo")
def resumo(repo: Repositorio = Depends(obter_repositorio)):
    """Quantas peças existem em cada papel.

    A tela de recomendação consulta isto antes de deixar o usuário pedir um look:
    é mais honesto avisar que falta calçado do que deixar o pedido falhar depois.
    """
    pecas = repo.listar_pecas(disponivel=True)
    contagem = {"superior": 0, "inferior": 0, "calcado": 0, "sobreposicao": 0}
    for p in pecas:
        if p["papel"] in contagem:
            contagem[p["papel"]] += 1
    faltando = [papel for papel in ("superior", "inferior", "calcado")
                if contagem[papel] == 0]
    return {
        "total": len(pecas),
        "por_papel": contagem,
        "faltando": faltando,
        "pode_recomendar": not faltando,
    }


@router.patch("/{peca_id}", response_model=PecaSaida)
def atualizar(peca_id: str, mudancas: PecaAtualizacao,
              repo: Repositorio = Depends(obter_repositorio)):
    """6.3.1 — edição de atributos e alteração de disponibilidade."""
    campos = mudancas.model_dump(exclude_unset=True, exclude_none=True)
    if not campos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nada para atualizar.")
    if "categoria" in campos and campos["categoria"] not in POR_CHAVE:
        raise HTTPException(HTTP_422,
                            f"Categoria desconhecida: {campos['categoria']}")

    atualizada = repo.atualizar_peca(peca_id, campos)
    if atualizada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Peça não encontrada.")
    return atualizada


@router.delete("/{peca_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(peca_id: str, repo: Repositorio = Depends(obter_repositorio)):
    """6.3.1 — remoção de uma peça do acervo."""
    if repo.remover_peca(peca_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Peça não encontrada.")
