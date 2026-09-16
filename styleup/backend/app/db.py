"""Escolha do repositório para a requisição.

Ponto importante do modo produção: usamos a chave **anônima** do Supabase e
injetamos o JWT do usuário. Assim as políticas de RLS continuam valendo dentro do
backend — se houver um erro de lógica numa rota, o banco ainda impede que um
usuário leia as peças de outro. Usar a service-role key aqui desligaria essa
proteção e transformaria qualquer bug em vazamento.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import Depends

from .auth import Usuario, usuario_atual
from .config import config
from .repositorio import Repositorio, RepositorioMemoria, RepositorioSupabase

log = logging.getLogger(__name__)

# Quantas sessões mantêm cliente próprio. Cada cliente carrega o seu pool de
# conexões HTTP; 64 cobre um uso acadêmico com folga e limita a memória.
MAX_CLIENTES = 64


@lru_cache(maxsize=MAX_CLIENTES)
def _cliente_para_token(token: str):
    """Um cliente Supabase por token de acesso.

    A versão anterior mantinha **um único** cliente em cache e chamava
    `postgrest.auth(token)` a cada requisição. Como o cliente é compartilhado,
    duas requisições simultâneas de usuários diferentes sobrescreviam o token uma
    da outra: a consulta de A podia sair autenticada como B. Com RLS ativa isso é
    exatamente um vazamento de dados entre contas — o pior defeito do projeto, e
    invisível em teste sequencial.

    Agora o token faz parte da chave do cache, então cada sessão tem o seu
    cliente e o pool de conexões continua sendo reaproveitado entre requisições
    do mesmo usuário.
    """
    from supabase import create_client        # import tardio: o modo demo não precisa
    from supabase.lib.client_options import ClientOptions

    cliente = create_client(
        config.supabase_url,
        config.supabase_anon_key,
        options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
    )
    # Redundante com o header acima em versões recentes do SDK, mas garante o
    # comportamento em versões que só leem a sessão do PostgREST.
    cliente.postgrest.auth(token)
    return cliente


@lru_cache(maxsize=1)
def _cliente_anonimo():
    from supabase import create_client

    return create_client(config.supabase_url, config.supabase_anon_key)


def limpar_clientes() -> None:
    """Descarta os clientes em cache. Usado nos testes e ao recarregar config."""
    _cliente_para_token.cache_clear()
    _cliente_anonimo.cache_clear()


def obter_repositorio(usuario: Usuario = Depends(usuario_atual)) -> Repositorio:
    """Dependência das rotas. Devolve um repositório já escopado ao usuário."""
    if config.modo_demo:
        return RepositorioMemoria(usuario.id)

    cliente = _cliente_para_token(usuario.token) if usuario.token else _cliente_anonimo()
    return RepositorioSupabase(cliente, usuario.id)
