"""Configuração comum dos testes.

Todos rodam em modo demonstração: sem rede, sem Supabase, sem credenciais. É o
que permite a suíte inteira terminar em menos de um segundo e rodar em qualquer
máquina — inclusive na integração contínua.
"""

from __future__ import annotations

import os

import pytest

# Precisa vir antes de qualquer import de app.config, que lê o ambiente na carga.
os.environ["MODO_DEMO"] = "true"
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_ANON_KEY", None)
os.environ.pop("SUPABASE_JWT_SECRET", None)

from fastapi.testclient import TestClient          # noqa: E402

from app import config as modulo_config            # noqa: E402
from app.main import app                           # noqa: E402
from app.repositorio import limpar_armazens        # noqa: E402

modulo_config.recarregar()


@pytest.fixture(autouse=True)
def armazem_limpo():
    """Cada teste começa com o guarda-roupa de exemplo intacto."""
    limpar_armazens()
    yield
    limpar_armazens()


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)
