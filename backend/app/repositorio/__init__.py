"""Escolha do repositório por requisição e verificação de consentimento."""

from __future__ import annotations

import threading
import time
from typing import Iterator

from fastapi import Depends

from ..auth import Usuario, usuario_atual
from ..config import config
from ..erros import ErroAPI
from .base import Repositorio
from .memoria import RepositorioMemoria, armazem

__all__ = ["Repositorio", "RepositorioMemoria", "armazem", "obter_repositorio",
           "com_consentimento", "esquecer_consentimento", "consentimento_vigente",
           "localizacao_autorizada"]


def obter_repositorio(usuario: Usuario = Depends(usuario_atual)) -> Iterator[Repositorio]:
    """Um repositório novo a cada requisição, autenticado como quem chamou.

    Nada é compartilhado entre requisições: é isso que impede uma consulta de
    sair com o token de outro usuário quando duas chegam ao mesmo tempo.
    """
    if usuario.demo:
        yield RepositorioMemoria(usuario, semear=True)
        return
    from .supabase import RepositorioSupabase   # import tardio: o modo demo não precisa

    repo = RepositorioSupabase(usuario)
    try:
        yield repo
    finally:
        repo.fechar()


# Consentimento já conferido, por usuário. Evita uma ida ao banco em toda
# requisição (a recomendação tem orçamento de 3 s). Só respostas positivas são
# guardadas; revogar ou excluir a conta apaga a entrada na hora, neste processo.
_VALIDADE = 600.0
_conferidos: dict[str, tuple[float, dict]] = {}
_trava = threading.Lock()


def esquecer_consentimento(usuario_id: str) -> None:
    with _trava:
        _conferidos.pop(usuario_id, None)


def consentimento_vigente(repo: Repositorio) -> dict | None:
    """O aceite em vigor do usuário: versão atual do termo e não revogado."""
    atual = repo.consentimento()
    if (atual and atual.get("versao") == config.versao_termo
            and not atual.get("revogado_em")):
        return atual
    return None


def com_consentimento(repo: Repositorio = Depends(obter_repositorio)) -> Repositorio:
    """Dependência das rotas que tratam dados pessoais (LGPD, art. 7º, I).

    Sem aceite da versão vigente do termo, a rota responde 403 com o código
    `consentimento_pendente`, e a interface leva o usuário à tela do termo.
    """
    if not config.exigir_consentimento:
        return repo
    uid = repo.usuario.id
    agora = time.monotonic()
    with _trava:
        guardado = _conferidos.get(uid)
    if guardado and agora - guardado[0] < _VALIDADE:
        return repo
    vigente = consentimento_vigente(repo)
    if not vigente:
        raise ErroAPI(403, "consentimento_pendente",
                      "Para continuar, leia e aceite o termo de uso dos seus dados.",
                      versao=config.versao_termo)
    with _trava:
        _conferidos[uid] = (agora, vigente.get("finalidades") or {})
    return repo


def localizacao_autorizada(repo: Repositorio) -> bool:
    """O usuário aceitou a finalidade opcional de localização?"""
    if not config.exigir_consentimento:
        return True
    with _trava:
        guardado = _conferidos.get(repo.usuario.id)
    finalidades = guardado[1] if guardado else (consentimento_vigente(repo) or {}).get(
        "finalidades") or {}
    return bool(finalidades.get("localizacao"))
