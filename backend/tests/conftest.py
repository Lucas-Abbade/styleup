"""Configuração comum dos testes.

Tudo roda sem rede e sem Supabase: as rotas usam o repositório em memória (o
mesmo do modo demonstração), que replica as regras do banco.
"""

from __future__ import annotations

import os

# Antes de importar a aplicação: variáveis do Supabase definidas na máquina de
# quem roda os testes não podem vazar para cá (já confundiu o time uma vez).
for _nome in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET"):
    os.environ.pop(_nome, None)
os.environ.update(MODO_DEMO="true", AQUECER_MODELOS="false", AMBIENTE="teste",
                  EXIGIR_CONSENTIMENTO="true")

import pytest
from fastapi.testclient import TestClient

from app import repositorio
from app.config import config
from app.main import app
from app.repositorio.memoria import armazem, peca_de_exemplo
from app.services import clima


@pytest.fixture(autouse=True)
def _estado_limpo():
    armazem.limpar()
    repositorio._conferidos.clear()
    clima.limpar_cache()
    yield
    armazem.limpar()


@pytest.fixture
def cliente():
    with TestClient(app) as c:
        yield c


def cabecalho(nome: str) -> dict:
    return {"Authorization": f"Bearer demo:{nome}"}


def aceitar(cliente, nome: str, localizacao: bool = False) -> dict:
    """Usuário de teste com o termo aceito e o guarda-roupa de exemplo."""
    h = cabecalho(nome)
    r = cliente.post("/perfil/consentimento", headers=h,
                     json={"versao": config.versao_termo, "localizacao": localizacao})
    assert r.status_code == 201, r.text
    return h


@pytest.fixture
def ana(cliente):
    return aceitar(cliente, "ana")


@pytest.fixture
def bruno(cliente):
    return aceitar(cliente, "bruno")


@pytest.fixture
def vazio(cliente):
    """Usuário com consentimento e SEM peças (apaga o guarda-roupa de exemplo)."""
    h = aceitar(cliente, "vazio")
    for p in cliente.get("/pecas", headers=h).json():
        assert cliente.delete(f"/pecas/{p['id']}", headers=h).status_code == 204
    return h


def nova_peca(categoria="camiseta", cor="preto", **extras) -> dict:
    return {**peca_de_exemplo(categoria, cor), **extras}
