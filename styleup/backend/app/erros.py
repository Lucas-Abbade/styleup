"""Tratamento e formatação global de erros.

Regra única: **toda** resposta de erro da API tem a forma

    {"detail": "<texto em português para o usuário>", "requisicao": "<id>"}

O `detail` existe porque é o que o FastAPI usa nativamente e o que o cliente do
frontend já lê (`extrairMensagem` em `lib/api.ts`). O `requisicao` é o mesmo id
que aparece no log e no cabeçalho `X-Requisicao`, para que um relato de bug possa
ser cruzado com a linha exata do log.

O que isso resolve na prática: antes, um erro de validação do Pydantic chegava à
tela como uma lista de objetos em inglês (`[{"loc": [...], "msg": "Input should
be a valid integer"}]`), e uma exceção não prevista virava um 500 sem rastro.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("styleup.erros")

CABECALHO_REQUISICAO = "X-Requisicao"

# Tradução das mensagens que o Pydantic emite com mais frequência nesta API.
# Só as que o usuário pode de fato provocar: o resto cai no texto genérico.
TRADUCOES = {
    "field required": "campo obrigatório",
    "Field required": "campo obrigatório",
    "Input should be a valid integer": "informe um número inteiro",
    "Input should be a valid number": "informe um número",
    "Input should be a valid string": "informe um texto",
    "Input should be a valid boolean": "informe verdadeiro ou falso",
    "Input should be a valid list": "informe uma lista",
    "Extra inputs are not permitted": "campo não reconhecido",
    "Input should be 'superior', 'inferior', 'calcado' or 'sobreposicao'":
        "papel deve ser superior, inferior, calcado ou sobreposicao",
}


def _traduzir(msg: str) -> str:
    if msg in TRADUCOES:
        return TRADUCOES[msg]
    # mensagens paramétricas do Pydantic
    if "greater than or equal to" in msg:
        return msg.replace("Input should be greater than or equal to",
                           "o valor mínimo é")
    if "less than or equal to" in msg:
        return msg.replace("Input should be less than or equal to",
                           "o valor máximo é")
    if "should have at least" in msg:
        return msg.replace("List should have at least", "a lista deve ter ao menos") \
                  .replace("items after validation, not", "itens, e tem")
    if "should have at most" in msg:
        return msg.replace("List should have at most", "a lista deve ter no máximo") \
                  .replace("items after validation, not", "itens, e tem")
    return msg


def _campo(loc: tuple) -> str:
    """Nome legível do campo, sem o prefixo técnico ('body', 'query')."""
    partes = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(partes) or "corpo da requisição"


def id_da_requisicao(request: Request) -> str:
    return getattr(request.state, "requisicao", "-")


def registrar(app: FastAPI) -> None:
    """Instala os handlers. Chamado uma vez, em `main.py`."""

    @app.middleware("http")
    async def marcar_requisicao(request: Request, call_next):
        """Dá um id a cada requisição, antes de qualquer coisa poder falhar."""
        request.state.requisicao = uuid.uuid4().hex[:12]
        resposta = await call_next(request)
        resposta.headers[CABECALHO_REQUISICAO] = request.state.requisicao
        return resposta

    @app.exception_handler(RequestValidationError)
    async def validacao(request: Request, exc: RequestValidationError):
        problemas = [
            f"{_campo(erro.get('loc', ()))}: {_traduzir(str(erro.get('msg', '')))}"
            for erro in exc.errors()
        ]
        detalhe = "Dados inválidos. " + "; ".join(problemas[:4]) + "."
        log.info("422 %s %s | %s", request.method, request.url.path, problemas)
        return JSONResponse(
            status_code=422,
            content={"detail": detalhe, "requisicao": id_da_requisicao(request)},
            headers={CABECALHO_REQUISICAO: id_da_requisicao(request)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http(request: Request, exc: StarletteHTTPException):
        """Mantém o status e a mensagem da rota, só uniformiza o envelope."""
        detalhe = exc.detail if isinstance(exc.detail, str) else jsonable_encoder(exc.detail)
        if exc.status_code >= 500:
            log.error("%s %s %s | %s", exc.status_code, request.method,
                      request.url.path, detalhe)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detalhe, "requisicao": id_da_requisicao(request)},
            headers={**(exc.headers or {}),
                     CABECALHO_REQUISICAO: id_da_requisicao(request)},
        )

    @app.exception_handler(Exception)
    async def inesperado(request: Request, exc: Exception):
        """Rede de segurança: nada escapa como 500 sem log e sem id.

        A mensagem ao usuário é deliberadamente vaga — detalhe interno em tela é
        superfície de ataque —, mas o id devolvido localiza o traceback no log.
        """
        rid = id_da_requisicao(request)
        log.exception("500 %s %s | requisicao=%s", request.method, request.url.path, rid)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Erro interno no servidor. Tente novamente em instantes.",
                "requisicao": rid,
            },
            headers={CABECALHO_REQUISICAO: rid},
        )
