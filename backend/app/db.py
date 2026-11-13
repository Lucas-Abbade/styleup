"""Acesso ao Supabase a partir do backend.

Ponto importante: usamos a chave **anônima** e injetamos o JWT do usuário na
sessão do PostgREST. Com isso as políticas de RLS continuam valendo dentro do
backend — se houver um erro de lógica numa rota, o banco ainda impede que um
usuário leia as peças de outro. Usar a service-role key aqui desligaria essa
proteção e transformaria qualquer bug em vazamento.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from .auth import Usuario
from .config import config


@lru_cache(maxsize=1)
def _cliente_base() -> Client:
    if not config.configurado:
        raise RuntimeError(
            "Supabase não configurado. Defina SUPABASE_URL, SUPABASE_ANON_KEY e "
            "SUPABASE_JWT_SECRET no arquivo .env."
        )
    return create_client(config.supabase_url, config.supabase_anon_key)


def como_usuario(usuario: Usuario) -> Client:
    """Cliente autenticado como o usuário da requisição."""
    cliente = _cliente_base()
    cliente.postgrest.auth(usuario.token)
    return cliente


def proximo_codigo(cliente: Client, usuario_id: str) -> str:
    resposta = cliente.rpc("proximo_codigo_peca", {"p_usuario": usuario_id}).execute()
    return resposta.data or "CLO-000001"
