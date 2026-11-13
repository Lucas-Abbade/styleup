"""Aplicação FastAPI do StyleUp.

Executar em desenvolvimento:
    uvicorn app.main:app --reload --port 8000

Documentação interativa: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .routers import feedback, pecas, recomendacao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)

app = FastAPI(
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

    Sem isto, "5 segundos para catalogar" vira opinião. 
    """
    inicio = time.perf_counter()
    resposta = await call_next(request)
    duracao_ms = (time.perf_counter() - inicio) * 1000
    resposta.headers["X-Tempo-ms"] = f"{duracao_ms:.0f}"
    if duracao_ms > 3000:
        logging.getLogger("desempenho").warning(
            "%s %s levou %.0f ms", request.method, request.url.path, duracao_ms)
    return resposta


app.include_router(pecas.router)
app.include_router(recomendacao.router)
app.include_router(feedback.router)


@app.get("/saude", tags=["infra"])
def saude():
    """Sonda de disponibilidade, usada pelo Docker e pela hospedagem."""
    return {
        "status": "ok",
        "ambiente": config.ambiente,
        "supabase_configurado": config.configurado,
    }
