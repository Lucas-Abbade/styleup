"""Rotas exclusivas do modo demonstração.

Só são montadas quando `config.modo_demo` está ligado (nunca em produção). No
modo real, o navegador envia e lê as fotos direto do Storage do Supabase; aqui
o próprio backend faz esse papel, em memória.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from ..erros import ErroAPI
from ..repositorio import Repositorio, armazem, obter_repositorio

router = APIRouter(prefix="/demo", tags=["demonstração"])

TAMANHO_MAXIMO = 4 * 1024 * 1024


@router.post("/fotos", status_code=201)
def enviar_foto(foto: UploadFile = File(...),
                repo: Repositorio = Depends(obter_repositorio)):
    conteudo = foto.file.read(TAMANHO_MAXIMO + 1)
    if len(conteudo) > TAMANHO_MAXIMO:
        raise ErroAPI(413, "foto_grande_demais", "Foto maior que 4 MB.")
    return {"caminho": repo.salvar_foto(conteudo, foto.content_type or "image/jpeg")}


@router.get("/fotos/{caminho:path}")
def ler_foto(caminho: str):
    """Sem autenticação porque `<img>` não envia cabeçalho; o caminho tem um
    UUID aleatório, como uma URL assinada, e os dados são de demonstração."""
    guardada = armazem.fotos.get(caminho)
    if not guardada:
        raise ErroAPI(404, "foto_nao_encontrada", "Foto não encontrada.")
    return Response(guardada[0], media_type=guardada[1],
                    headers={"Cache-Control": "private, max-age=3600"})


@router.post("/reiniciar")
def reiniciar(repo: Repositorio = Depends(obter_repositorio)):
    """Volta o visitante ao guarda-roupa de exemplo (útil antes de apresentar)."""
    repo.excluir_conta()
    return {"reiniciado": True}
