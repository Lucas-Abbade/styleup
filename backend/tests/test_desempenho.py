"""Fase 3: a API não pode travar enquanto uma requisição pesada roda."""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from app.config import config
from app.main import app
from app.services import visao

from .conftest import cabecalho

ATRASO = 0.6


@pytest.mark.asyncio
async def test_analise_lenta_nao_bloqueia_a_api(monkeypatch):
    """Item 1: `/pecas/analisar` era `async def` com trabalho bloqueante (CPU do
    FashionCLIP); a API inteira parava — até o /saude. Duas análises simultâneas
    devem levar o tempo de uma, e o /saude deve responder no meio delas."""
    def analise_lenta(dados, com_recorte=True):
        time.sleep(ATRASO)                       # trabalho bloqueante, como o modelo
        return {
            "categoria": "polo", "rotulo": "Camisa polo", "papel": "superior",
            "formalidade": 3, "temp_min": 18, "temp_max": 40, "resiste_chuva": True,
            "atributos": {}, "cor_nome": "preto", "cor_hex": "#000000",
            "cor_hsv": [0, 0, 0], "neutra": True, "confianca": {},
        }
    monkeypatch.setattr(visao, "analisar", analise_lenta)

    transporte = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as c:
        h = cabecalho("perf")
        r = await c.post("/perfil/consentimento", headers=h,
                         json={"versao": config.versao_termo})
        assert r.status_code == 201

        async def analisar():
            return await c.post("/pecas/analisar", headers=h,
                                files={"foto": ("p.jpg", b"x", "image/jpeg")})

        async def saude():
            await asyncio.sleep(0.1)             # chega com as análises em curso
            inicio = time.perf_counter()
            resposta = await c.get("/saude")
            return resposta, time.perf_counter() - inicio

        inicio = time.perf_counter()
        a, b, (s, tempo_saude) = await asyncio.gather(analisar(), analisar(), saude())
        total = time.perf_counter() - inicio

    assert a.status_code == b.status_code == 200 and s.status_code == 200
    assert tempo_saude < ATRASO / 2, f"/saude esperou {tempo_saude:.2f} s pela análise"
    assert total < ATRASO * 1.7, f"as duas análises rodaram em série ({total:.2f} s)"
    assert a.headers["x-tempo-ms"]


def test_recomendacao_responde_dentro_do_orcamento(cliente, ana):
    """RNF02 (3 s). Sem rede, o que se mede aqui é o motor + a API."""
    tempos = []
    for _ in range(10):
        r = cliente.post("/recomendacoes", headers=ana, json={"evento": "casual"})
        assert r.status_code == 200
        tempos.append(float(r.headers["x-tempo-ms"]))
    assert sorted(tempos)[-1] < 500, tempos


def test_saude_informa_o_estado_dos_modelos(cliente):
    corpo = cliente.get("/saude").json()
    assert corpo["status"] == "ok" and corpo["modo_demo"] is True
    assert corpo["visao"]["situacao"] in ("frio", "aquecendo", "pronto", "indisponivel")
