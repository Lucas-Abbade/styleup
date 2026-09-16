"""Testes da integração de clima.

Nada aqui toca a rede: substituímos o cliente HTTP. O objetivo é travar o
comportamento de degradação (RNF07) e o cache, que são justamente as partes que
um teste com rede real não conseguiria exercitar de forma confiável.
"""

from __future__ import annotations

import httpx
import pytest

from app.services import clima


@pytest.fixture(autouse=True)
def cache_limpo():
    clima.limpar_cache()
    yield
    clima.limpar_cache()


class ClienteFalso:
    """Substituto do AsyncClient que conta chamadas e pode falhar sob comando."""

    def __init__(self, temperatura=23.0, chuva=30, falhar=False):
        self.chamadas = 0
        self.temperatura = temperatura
        self.chuva = chuva
        self.falhar = falhar
        self.is_closed = False

    async def get(self, url, params=None):
        self.chamadas += 1
        if self.falhar:
            raise httpx.ConnectError("rede indisponível")
        # `request=` é obrigatório: sem ele, `raise_for_status()` lança
        # TypeError e o teste mede o caminho de falha, não o de sucesso.
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={
                "current": {
                    "temperature_2m": self.temperatura,
                    "apparent_temperature": self.temperatura + 2,
                    "precipitation_probability": self.chuva,
                }
            },
        )


@pytest.fixture
def cliente_falso(monkeypatch):
    falso = ClienteFalso()

    async def obter():
        return falso

    monkeypatch.setattr(clima, "_obter_cliente", obter)
    return falso


# ------------------------------------------------------------- leitura
@pytest.mark.asyncio
async def test_converte_a_probabilidade_para_fracao(cliente_falso):
    """A API devolve 0-100; o motor trabalha com 0-1."""
    atual = await clima.previsao(-23.55, -46.63)
    assert atual == {"temperatura": 23.0, "sensacao": 25.0, "chuva_prob": 0.30}


@pytest.mark.asyncio
async def test_probabilidade_ausente_vira_none(monkeypatch):
    falso = ClienteFalso(chuva=None)

    async def obter():
        return falso

    monkeypatch.setattr(clima, "_obter_cliente", obter)
    atual = await clima.previsao(-23.55, -46.63)
    assert atual["chuva_prob"] is None


# --------------------------------------------------------------- cache
@pytest.mark.asyncio
async def test_segunda_consulta_na_mesma_celula_usa_o_cache(cliente_falso):
    await clima.previsao(-23.5505, -46.6333)
    await clima.previsao(-23.5505, -46.6333)
    assert cliente_falso.chamadas == 1


@pytest.mark.asyncio
async def test_coordenadas_proximas_caem_na_mesma_celula(cliente_falso):
    """Duas pessoas no mesmo quarteirão não geram duas chamadas externas."""
    await clima.previsao(-23.5501, -46.6331)
    await clima.previsao(-23.5504, -46.6334)
    assert cliente_falso.chamadas == 1


@pytest.mark.asyncio
async def test_cidades_diferentes_geram_chamadas_diferentes(cliente_falso):
    await clima.previsao(-23.55, -46.63)     # São Paulo
    await clima.previsao(-22.91, -43.17)     # Rio de Janeiro
    assert cliente_falso.chamadas == 2


@pytest.mark.asyncio
async def test_cache_vencido_gera_nova_chamada(cliente_falso, monkeypatch):
    await clima.previsao(-23.55, -46.63)
    # avança o relógio além da validade
    original = clima.time.monotonic
    monkeypatch.setattr(clima.time, "monotonic",
                        lambda: original() + clima.VALIDADE_CACHE + 1)
    await clima.previsao(-23.55, -46.63)
    assert cliente_falso.chamadas == 2


@pytest.mark.asyncio
async def test_cache_nao_cresce_sem_limite(cliente_falso):
    for i in range(clima.MAX_CACHE + 20):
        await clima.previsao(-23.0 + i * 0.5, -46.0)
    assert len(clima._cache) <= clima.MAX_CACHE


# ----------------------------------------------------------- degradação
@pytest.mark.asyncio
async def test_falha_de_rede_devolve_none_em_vez_de_explodir(monkeypatch):
    """RNF07: a recomendação segue sem clima, não quebra."""
    falso = ClienteFalso(falhar=True)

    async def obter():
        return falso

    monkeypatch.setattr(clima, "_obter_cliente", obter)
    assert await clima.previsao(-23.55, -46.63) is None


@pytest.mark.asyncio
async def test_falha_apos_leitura_boa_reaproveita_o_valor_vencido(cliente_falso,
                                                                 monkeypatch):
    """Um dado de dez minutos atrás descreve o clima melhor que nenhum dado."""
    await clima.previsao(-23.55, -46.63)

    original = clima.time.monotonic
    monkeypatch.setattr(clima.time, "monotonic",
                        lambda: original() + clima.VALIDADE_CACHE + 1)
    cliente_falso.falhar = True

    atual = await clima.previsao(-23.55, -46.63)
    assert atual is not None
    assert atual["temperatura"] == 23.0
