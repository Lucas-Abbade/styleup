"""Testes de isolamento entre usuários.

Cobrem o defeito mais grave que a auditoria encontrou: o cliente do Supabase era
um singleton e recebia o token do usuário por mutação
(`cliente.postgrest.auth(token)`). Duas requisições simultâneas de contas
diferentes sobrescreviam o token uma da outra, e a consulta de A podia sair
autenticada como B — vazamento de dados entre contas, invisível em teste
sequencial.

Os testes rodam sem Supabase: substituímos `create_client` por um duplo que
registra com que credencial cada cliente foi construído.
"""

from __future__ import annotations

import asyncio
import sys
import types

import pytest

from app import config as modulo_config
from app import db
from app.auth import Usuario


class ClienteFalso:
    """Registra o token com que foi criado e as mutações que sofreu."""

    def __init__(self, url, chave, options=None):
        self.url = url
        self.chave = chave
        self.token_das_opcoes = (options or {}).get("headers", {}).get("Authorization")
        self.tokens_aplicados: list[str] = []
        self.postgrest = types.SimpleNamespace(auth=self.tokens_aplicados.append)


@pytest.fixture
def supabase_falso(monkeypatch):
    """Faz o modo produção usar um SDK de mentira."""
    criados: list[ClienteFalso] = []

    def create_client(url, chave, options=None):
        cliente = ClienteFalso(url, chave, options)
        criados.append(cliente)
        return cliente

    class OpcoesFalsas(dict):
        def __init__(self, headers=None):
            super().__init__(headers=headers or {})

    modulo = types.ModuleType("supabase")
    modulo.create_client = create_client
    modulo.Client = ClienteFalso
    lib = types.ModuleType("supabase.lib")
    opcoes = types.ModuleType("supabase.lib.client_options")
    opcoes.ClientOptions = OpcoesFalsas
    monkeypatch.setitem(sys.modules, "supabase", modulo)
    monkeypatch.setitem(sys.modules, "supabase.lib", lib)
    monkeypatch.setitem(sys.modules, "supabase.lib.client_options", opcoes)

    # sai do modo demonstração
    monkeypatch.setenv("MODO_DEMO", "false")
    monkeypatch.setenv("SUPABASE_URL", "https://projeto.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "chave-anonima")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "segredo")
    modulo_config.recarregar()
    db.limpar_clientes()

    yield criados

    db.limpar_clientes()
    monkeypatch.undo()
    modulo_config.recarregar()


def test_modo_producao_e_realmente_ativado(supabase_falso):
    assert modulo_config.config.modo_demo is False
    assert modulo_config.config.supabase_configurado is True


def test_tokens_diferentes_recebem_clientes_diferentes(supabase_falso):
    """O coração da correção: nenhum objeto compartilhado entre sessões."""
    ana = db.obter_repositorio(Usuario(id="ana", email="a@x", token="jwt-da-ana"))
    bruno = db.obter_repositorio(Usuario(id="bruno", email="b@x", token="jwt-do-bruno"))

    assert ana._c is not bruno._c
    assert ana._c.token_das_opcoes == "Bearer jwt-da-ana"
    assert bruno._c.token_das_opcoes == "Bearer jwt-do-bruno"


def test_mesmo_token_reaproveita_o_cliente(supabase_falso):
    """O pool de conexões continua sendo reutilizado dentro de uma sessão."""
    primeiro = db.obter_repositorio(Usuario(id="ana", email="a@x", token="jwt-da-ana"))
    segundo = db.obter_repositorio(Usuario(id="ana", email="a@x", token="jwt-da-ana"))

    assert primeiro._c is segundo._c
    assert len(supabase_falso) == 1


def test_repositorio_carrega_o_id_do_usuario(supabase_falso):
    repo = db.obter_repositorio(Usuario(id="ana", email="a@x", token="jwt"))
    assert repo._uid == "ana"


def test_token_nao_vaza_entre_requisicoes_concorrentes(supabase_falso):
    """Reproduz o cenário que o defeito original quebrava.

    Muitas sessões pedindo repositório ao mesmo tempo: cada uma tem de terminar
    com o seu próprio token. Com o singleton anterior, o último `auth()` a
    executar valia para todos.
    """
    async def pedir(nome: str):
        # cede o controle no meio, como uma requisição real faria
        await asyncio.sleep(0)
        repo = db.obter_repositorio(Usuario(id=nome, email=f"{nome}@x",
                                            token=f"jwt-{nome}"))
        await asyncio.sleep(0)
        return nome, repo._c.token_das_opcoes

    async def rodar():
        nomes = [f"u{i}" for i in range(30)]
        return await asyncio.gather(*(pedir(n) for n in nomes))

    for nome, token in asyncio.run(rodar()):
        assert token == f"Bearer jwt-{nome}", (
            f"{nome} terminou autenticado com {token}")


def test_cache_de_clientes_e_limitado(supabase_falso):
    """Sessões novas não podem crescer a memória sem limite."""
    for i in range(db.MAX_CLIENTES + 25):
        db.obter_repositorio(Usuario(id=f"u{i}", email="x@x", token=f"jwt-{i}"))
    assert db._cliente_para_token.cache_info().currsize <= db.MAX_CLIENTES


def test_sem_token_usa_cliente_anonimo(supabase_falso):
    """Requisição sem token não deve reaproveitar o cliente de ninguém."""
    repo = db.obter_repositorio(Usuario(id="anon", email=None, token=None))
    assert repo._c.token_das_opcoes is None
