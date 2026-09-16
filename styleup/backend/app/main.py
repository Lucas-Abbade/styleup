"""Aplicação FastAPI do StyleUp.

Executar em desenvolvimento:
    uvicorn app.main:app --reload --port 8000

Documentação interativa: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import time

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import erros
from .config import config
from .routers import feedback, pecas, recomendacao
from .services import clima, visao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)

@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Deixa explícito no log em que modo a API subiu.

    Rodar em demonstração sem perceber, e concluir que o Supabase está
    integrado, é o mal-entendido mais caro possível às vésperas de uma entrega.
    """
    log = logging.getLogger("styleup")
    if config.modo_demo:
        motivo = ("MODO_DEMO=true" if config.forcar_demo
                  else "credenciais do Supabase ausentes")
        log.warning(
            "API em MODO DEMONSTRACAO (%s): dados em memoria, autenticacao "
            "desligada e guarda-roupa de exemplo carregado. Nao use em producao.",
            motivo)
    else:
        log.info("API conectada ao Supabase em %s", config.supabase_url)

    yield

    # sem isto, o cliente HTTP compartilhado do clima deixa sockets abertos ao
    # recarregar o uvicorn em desenvolvimento
    await clima.fechar_cliente()


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="StyleUp API",
    version="0.1.0",
    description=(
        "Catalogação de vestuário por foto e recomendação de looks conforme "
        "clima e ocasião. Módulos M2 a M6 do Documento de Visão."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.origens_permitidas),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def medir_tempo(request: Request, call_next):
    """Instrumentação dos RNF01 e RNF02: o tempo de resposta vai no cabeçalho.

    Sem isto, "5 segundos para catalogar" vira opinião. Com isto, o time coleta
    os percentis direto do log a partir do primeiro dia.
    """
    inicio = time.perf_counter()
    resposta = await call_next(request)
    duracao_ms = (time.perf_counter() - inicio) * 1000
    resposta.headers["X-Tempo-ms"] = f"{duracao_ms:.0f}"
    if duracao_ms > 3000:
        logging.getLogger("desempenho").warning(
            "%s %s levou %.0f ms", request.method, request.url.path, duracao_ms)
    return resposta


# Handlers globais antes das rotas: o middleware de id precisa envolver tudo.
erros.registrar(app)

app.include_router(pecas.router)
app.include_router(recomendacao.router)
app.include_router(feedback.router)


@app.get("/saude", tags=["infra"])
def saude():
    """Sonda de disponibilidade, usada pelo Docker e pela hospedagem."""
    return {
        "status": "ok",
        "ambiente": config.ambiente,
        "modo_demo": config.modo_demo,
        "supabase_configurado": config.supabase_configurado,
        "visao_disponivel": visao.modelo_disponivel(),
    }
