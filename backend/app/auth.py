"""Autenticação: validamos o JWT que o Supabase Auth emitiu para o frontend.

Projetos novos do Supabase assinam com chave assimétrica (ES256), verificada
pela chave pública publicada em /.well-known/jwks.json. Projetos antigos usam
HS256 com o JWT Secret. Aceitamos os dois.
"""

from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import config

esquema = HTTPBearer(auto_error=False)


class Usuario:
    def __init__(self, id: str, email: str | None, token: str):
        self.id = id
        self.email = email
        self.token = token          # repassado ao PostgREST para a RLS valer


@lru_cache(maxsize=1)
def _jwks() -> PyJWKClient:
    print("DEBUG url:", repr(config.supabase_url), flush=True)  # apagar depois
    return PyJWKClient(f"{config.supabase_url}/auth/v1/.well-known/jwks.json")


def _chave_e_algoritmos(token: str):
    alg = jwt.get_unverified_header(token).get("alg")
    if alg == "HS256":
        return config.supabase_jwt_secret, ["HS256"]
    if alg in ("ES256", "RS256"):
        return _jwks().get_signing_key_from_jwt(token).key, [alg]
    raise jwt.InvalidTokenError(f"algoritmo não aceito: {alg}")


def usuario_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema),
) -> Usuario:
    if credencial is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Envie o token de acesso no cabeçalho Authorization.")
    token = credencial.credentials
    try:
        chave, algoritmos = _chave_e_algoritmos(token)
        dados = jwt.decode(token, chave, algorithms=algoritmos,
                           audience="authenticated")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada.")
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token inválido: {exc}")

    sub = dados.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sem identificação de usuário.")
    return Usuario(id=sub, email=dados.get("email"), token=token)