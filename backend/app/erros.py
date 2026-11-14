"""Formato único de erro da API.

Toda resposta de erro tem o mesmo corpo:

    {"erro": "mensagem para o usuário", "codigo": "identificador_estavel"}

`erro` é texto em português, pronto para aparecer na tela. `codigo` é o que a
interface e os testes comparam — o texto pode ser reescrito sem quebrar ninguém.
`detail` repete a mensagem por compatibilidade com clientes antigos, que liam o
campo padrão do FastAPI.

Erros inesperados nunca devolvem stack trace: o detalhe vai para o log, com um
identificador que o usuário pode informar ao suporte.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("styleup.erros")

CODIGO_POR_STATUS = {
    400: "requisicao_invalida",
    401: "nao_autenticado",
    403: "acesso_negado",
    404: "nao_encontrado",
    405: "metodo_nao_permitido",
    409: "conflito",
    413: "arquivo_grande_demais",
    415: "tipo_nao_suportado",
    422: "dados_invalidos",
    429: "muitas_requisicoes",
    500: "erro_interno",
    502: "servico_externo_falhou",
    503: "servico_indisponivel",
}


class ErroAPI(Exception):
    """Erro de negócio ou de infraestrutura já traduzido para o usuário."""

    def __init__(self, status: int, codigo: str, mensagem: str, **extras):
        self.status = status
        self.codigo = codigo
        self.mensagem = mensagem
        self.extras = extras
        super().__init__(mensagem)


def corpo(mensagem: str, codigo: str, **extras) -> dict:
    return {"erro": mensagem, "codigo": codigo, "detail": mensagem, **extras}


def _resposta(status: int, mensagem: str, codigo: str, cabecalhos=None, **extras):
    return JSONResponse(corpo(mensagem, codigo, **extras), status_code=status,
                        headers=cabecalhos)


_NOMES_DE_CAMPO = {"cor_hsv": "cor (HSV)", "cor_hex": "cor (hexadecimal)",
                   "formalidade": "formalidade", "papel": "papel",
                   "categoria": "categoria", "evento": "evento"}


def registrar(app: FastAPI) -> None:
    @app.exception_handler(ErroAPI)
    async def _erro_api(_: Request, exc: ErroAPI):
        return _resposta(exc.status, exc.mensagem, exc.codigo, **exc.extras)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        mensagem = exc.detail if isinstance(exc.detail, str) else "Requisição inválida."
        if exc.status_code == 404 and mensagem == "Not Found":
            mensagem = "Rota não encontrada."
        if exc.status_code == 405:
            mensagem = "Método não permitido nesta rota."
        return _resposta(exc.status_code, mensagem,
                         CODIGO_POR_STATUS.get(exc.status_code, "erro"),
                         cabecalhos=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError):
        campos = []
        for erro in exc.errors():
            local = [str(p) for p in erro.get("loc", ()) if p not in ("body", "query", "path")]
            campos.append({
                "campo": ".".join(local) or "corpo",
                "problema": erro.get("msg", "valor inválido").removeprefix("Value error, "),
            })
        primeiro = campos[0] if campos else {"campo": "corpo", "problema": "valor inválido"}
        nome = _NOMES_DE_CAMPO.get(primeiro["campo"].split(".")[0], primeiro["campo"])
        return _resposta(422, f"Dado inválido em {nome}: {primeiro['problema']}",
                         "dados_invalidos", campos=campos)

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception):
        protocolo = uuid.uuid4().hex[:12]
        log.exception("Erro não tratado [%s] em %s %s", protocolo,
                      request.method, request.url.path, exc_info=exc)
        return _resposta(500, "Algo deu errado do nosso lado. Tente de novo em instantes.",
                         "erro_interno", protocolo=protocolo)
