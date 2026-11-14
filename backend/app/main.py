"""Aplicação FastAPI do StyleUp.

Executar em desenvolvimento:
    uvicorn app.main:app --reload --port 8000

Documentação interativa: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import erros
from .config import config
from .routers import demo, feedback, pecas, perfil, recomendacao
from .services import visao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
log = logging.getLogger("styleup")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Aquece os modelos de visão em segundo plano na subida.

    Em thread própria: a API já atende enquanto rembg e FashionCLIP carregam, e
    /saude informa o andamento. Sem as dependências de visão instaladas, o
    aquecimento só registra "indisponível" e segue.
    """
    if config.modo_demo:
        log.warning("MODO DEMONSTRAÇÃO: dados em memória e login fictício. "
                    "Configure o Supabase no .env para usar dados reais.")
    if config.aquecer_modelos:
        threading.Thread(target=visao.aquecer, name="aquecer-visao", daemon=True).start()
    yield


app = FastAPI(
    title="StyleUp API",
    version="0.2.0",
    description=(
        "Catalogação de vestuário por foto e recomendação de looks conforme "
        "clima e ocasião. Módulos M2 a M6 do Documento de Visão."
    ),
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.origens_permitidas),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Tempo-ms"],
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
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path not in ("/saude",) and not request.url.path.startswith("/demo/fotos"):
        # respostas com dados pessoais não devem ficar em cache intermediário
        resposta.headers.setdefault("Cache-Control", "no-store")
    if duracao_ms > 3000:
        logging.getLogger("desempenho").warning(
            "%s %s levou %.0f ms", request.method, request.url.path, duracao_ms)
    return resposta


erros.registrar(app)

app.include_router(pecas.router)
app.include_router(recomendacao.router)
app.include_router(feedback.router)
app.include_router(perfil.router)
if config.modo_demo:
    app.include_router(demo.router)


@app.get("/saude", tags=["infra"])
def saude():
    """Sonda de disponibilidade, usada pelo Docker e pela hospedagem."""
    return {
        "status": "ok",
        "ambiente": config.ambiente,
        "supabase_configurado": config.configurado,
        "modo_demo": config.modo_demo,
        "visao": visao.estado(),
        "versao_termo": config.versao_termo,
    }
