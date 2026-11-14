"""Autenticação: validamos o JWT que o Supabase Auth emitiu para o frontend.

Projetos novos do Supabase assinam com chave assimétrica (ES256), verificada
pela chave pública publicada em /.well-known/jwks.json. Projetos antigos usam
HS256 com o JWT Secret. Aceitamos os dois.
"""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import config
from .erros import ErroAPI

log = logging.getLogger(__name__)

esquema = HTTPBearer(auto_error=False)

# Prefixo do token do modo demonstração. Só é aceito com `config.modo_demo`.
PREFIXO_DEMO = "demo"
_NAMESPACE_DEMO = uuid.UUID("5b1f1c2e-7a57-4e55-9c0d-57a1e0000001")


class Usuario:
    def __init__(self, id: str, email: str | None, token: str, demo: bool = False):
        self.id = id
        self.email = email
        self.token = token          # repassado ao PostgREST e ao Storage para a RLS valer
        self.demo = demo


@lru_cache(maxsize=1)
def _jwks() -> PyJWKClient:
    # cache de 10 min: uma rotação de chave no Supabase é percebida sem reinício
    return PyJWKClient(f"{config.supabase_url}/auth/v1/.well-known/jwks.json",
                       cache_keys=True, lifespan=600, timeout=5)


def _chave_e_algoritmos(token: str):
    alg = jwt.get_unverified_header(token).get("alg")
    if alg == "HS256":
        if not config.supabase_jwt_secret:
            raise jwt.InvalidTokenError("projeto sem JWT secret configurado")
        return config.supabase_jwt_secret, ["HS256"]
    if alg in ("ES256", "RS256"):
        return _jwks().get_signing_key_from_jwt(token).key, [alg]
    raise jwt.InvalidTokenError(f"algoritmo não aceito: {alg}")


def _usuario_demo(token: str) -> Usuario:
    """`demo` é o visitante padrão; `demo:ana` cria um usuário isolado (testes)."""
    nome = token.partition(":")[2] or "visitante"
    return Usuario(id=str(uuid.uuid5(_NAMESPACE_DEMO, nome)),
                   email=f"{nome}@demo.styleup.app", token=token, demo=True)


def usuario_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema),
) -> Usuario:
    if credencial is None:
        raise ErroAPI(401, "nao_autenticado",
                      "Envie o token de acesso no cabeçalho Authorization.")
    token = credencial.credentials

    if config.modo_demo and (token == PREFIXO_DEMO or token.startswith(PREFIXO_DEMO + ":")):
        return _usuario_demo(token)

    try:
        chave, algoritmos = _chave_e_algoritmos(token)
        opcoes = {"audience": "authenticated"}
        if config.supabase_url:
            opcoes["issuer"] = f"{config.supabase_url}/auth/v1"
        dados = jwt.decode(token, chave, algorithms=algoritmos, **opcoes)
    except jwt.ExpiredSignatureError:
        raise ErroAPI(401, "sessao_expirada", "Sua sessão expirou. Entre novamente.")
    except jwt.PyJWKClientConnectionError as exc:
        # não conseguimos buscar a chave pública: o problema é nosso, não do token
        log.error("Falha ao consultar o JWKS do Supabase: %s", exc)
        raise ErroAPI(503, "autenticacao_indisponivel",
                      "Não foi possível validar o acesso agora. Tente de novo em instantes.")
    except jwt.PyJWTError as exc:
        # o motivo vai para o log; a resposta não descreve a validação por dentro
        log.info("Token recusado: %s", exc)
        raise ErroAPI(401, "token_invalido", "Token de acesso inválido. Entre novamente.")

    sub = dados.get("sub")
    if not sub:
        raise ErroAPI(401, "token_invalido", "Token sem identificação de usuário.")
    return Usuario(id=sub, email=dados.get("email"), token=token)
