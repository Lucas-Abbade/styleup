"""Perfil, consentimento e direitos do titular (LGPD)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from ..config import config
from ..erros import ErroAPI
from ..repositorio import (
    Repositorio, consentimento_vigente, esquecer_consentimento, obter_repositorio,
)
from ..schemas import ConsentimentoEntrada, ExclusaoContaEntrada, PerfilAtualizacao
from ..services.recomendador import normalizar_pesos
from ..termo import termo

log = logging.getLogger(__name__)

router = APIRouter(prefix="/perfil", tags=["perfil"])

PALAVRA_DE_CONFIRMACAO = "EXCLUIR"


def _situacao(repo: Repositorio) -> dict:
    vigente = consentimento_vigente(repo)
    return {
        "versao_vigente": config.versao_termo,
        "aceito": vigente is not None,
        "aceito_em": vigente["aceito_em"] if vigente else None,
        "versao_aceita": vigente["versao"] if vigente else None,
        "localizacao": bool(((vigente or {}).get("finalidades") or {}).get("localizacao")),
        "exigido": config.exigir_consentimento,
    }


@router.get("")
def ler(repo: Repositorio = Depends(obter_repositorio)):
    """Dados da conta e situação do consentimento. Não exige aceite: é esta
    rota que diz à interface se a tela do termo precisa aparecer."""
    return {**repo.perfil(), "consentimento": _situacao(repo),
            "pesos": normalizar_pesos(repo.pesos())}


@router.put("")
def atualizar(entrada: PerfilAtualizacao, repo: Repositorio = Depends(obter_repositorio)):
    return {**repo.atualizar_perfil(entrada.nome), "consentimento": _situacao(repo)}


@router.get("/termo")
def ler_termo():
    """Texto e versão do termo em vigor. Público: é lido antes do aceite."""
    return termo()


@router.post("/consentimento", status_code=201)
def aceitar(entrada: ConsentimentoEntrada, repo: Repositorio = Depends(obter_repositorio)):
    """Registra o aceite: quem, quando, qual versão e quais finalidades.

    A versão vem do cliente e é conferida: aceitar um termo que não é o vigente
    (aba aberta desde ontem) não vale como consentimento informado.
    """
    if entrada.versao != config.versao_termo:
        raise ErroAPI(409, "termo_desatualizado",
                      "O termo foi atualizado. Recarregue e leia a versão atual.",
                      versao=config.versao_termo)
    repo.registrar_consentimento(entrada.versao, {
        "essencial": True, "localizacao": entrada.localizacao})
    esquecer_consentimento(repo.usuario.id)
    return _situacao(repo)


@router.delete("/consentimento")
def revogar(repo: Repositorio = Depends(obter_repositorio)):
    """Retira o consentimento (art. 8º, § 5º). Os dados ficam guardados, mas
    nada mais é tratado até novo aceite; para apagar, use a exclusão da conta."""
    repo.revogar_consentimento()
    esquecer_consentimento(repo.usuario.id)
    return _situacao(repo)


@router.get("/exportar")
def exportar(repo: Repositorio = Depends(obter_repositorio)):
    """Cópia dos dados do titular em formato estruturado (art. 18, II e V)."""
    return {"versao_formato": 1, **repo.exportar_dados()}


@router.delete("")
def excluir(entrada: ExclusaoContaEntrada, repo: Repositorio = Depends(obter_repositorio)):
    """Exclui a conta: registros no banco e toda a pasta do usuário no bucket.

    Pede a palavra de confirmação no corpo — um toque acidental não pode apagar
    um guarda-roupa inteiro.
    """
    if entrada.confirmacao.strip().upper() != PALAVRA_DE_CONFIRMACAO:
        raise ErroAPI(422, "confirmacao_invalida",
                      f"Digite {PALAVRA_DE_CONFIRMACAO} para confirmar a exclusão.")
    resultado = repo.excluir_conta()
    esquecer_consentimento(repo.usuario.id)
    log.info("Conta excluída: %d peças, %d fotos", resultado["pecas_removidas"],
             resultado["fotos_removidas"])
    return {"excluida": True, **resultado}
