"""Autenticação: validamos o JWT que o Supabase Auth emitiu para o frontend.

O backend não guarda senha nem emite token. Ele confere a assinatura e extrai o
`sub`, que é o `auth.uid()` usado nas políticas de RLS. Existe uma única fonte de
identidade no sistema.

No modo demonstração não há JWT para validar, então todas as requisições
respondem como um usuário fixo. O modo é anunciado em `/saude` e no log de
inicialização justamente porque desligar a autenticação sem aviso seria grave.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import config

# auto_error=False: em modo demonstração a ausência de token não é erro.
esquema = HTTPBearer(auto_error=False)

USUARIO_DEMO_ID = "00000000-0000-4000-8000-000000000001"
USUARIO_DEMO_EMAIL = "demonstracao@styleup.local"


@dataclass(frozen=True)
class Usuario:
    id: str
    email: str | None
    token: str | None = None       # repassado ao PostgREST para a RLS valer


def usuario_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema),
) -> Usuario:
    if config.modo_demo:
        return Usuario(id=USUARIO_DEMO_ID, email=USUARIO_DEMO_EMAIL)

    if credencial is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Envie o token de acesso no cabeçalho Authorization.")
    token = credencial.credentials
    try:
        dados = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token inválido: {exc}")

    sub = dados.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Token sem identificação de usuário.")
    return Usuario(id=sub, email=dados.get("email"), token=token)
