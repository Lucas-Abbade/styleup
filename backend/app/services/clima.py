"""Integração com a API de clima (módulo M4).

Open-Meteo não exige chave nem cadastro, o que atende ao RNF14 (nenhuma
dependência paga obrigatória). A falha da API não pode derrubar a recomendação:
o RNF07 manda cair para contexto informado manualmente, então aqui devolvemos
`None` em vez de propagar exceção.

Privacidade (LGPD, princípio da necessidade): a coordenada é arredondada para
duas casas (~1 km) antes de sair do servidor e não é gravada em lugar nenhum.
O mesmo arredondamento é a chave do cache.
"""

from __future__ import annotations

import logging
import threading
import time

import httpx

log = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 4.0            # a recomendação tem orçamento de 3 s (RNF02); não dá para esperar
VALIDADE_CACHE = 15 * 60  # segundos; a previsão horária não muda mais rápido que isso
HORAS_A_FRENTE = 3        # janela em que a chuva interessa a quem vai sair agora
_LIMITE_CACHE = 512

_cache: dict[tuple[float, float], tuple[float, dict]] = {}
_trava = threading.Lock()
_cliente: httpx.Client | None = None


def _http() -> httpx.Client:
    """Um cliente só, reaproveitando a conexão TLS entre consultas."""
    global _cliente
    if _cliente is None:
        _cliente = httpx.Client(timeout=TIMEOUT)
    return _cliente


def limpar_cache() -> None:
    with _trava:
        _cache.clear()


def _extrair(dados: dict) -> dict:
    """Converte a resposta da Open-Meteo no formato interno.

    A probabilidade de chuva vem da série horária (`hourly`), que é onde a
    documentação da Open-Meteo define o campo. A suspeita original era que ele
    não existisse em `current`; o código-fonte do servidor indica que existe,
    mas não foi possível testar ao vivo — e a série horária funciona nos dois
    cenários. Usamos o máximo das próximas horas porque quem pergunta "o que
    vestir" vai ficar na rua por um tempo, não por um instante.
    """
    atual = dados.get("current") or {}
    probabilidades = [p for p in (dados.get("hourly") or {})
                      .get("precipitation_probability", []) if p is not None]
    chuva = max(probabilidades) / 100 if probabilidades else None
    if chuva is None and (atual.get("precipitation") or 0) > 0:
        chuva = 1.0                      # sem previsão, mas já está chovendo
    return {
        "temperatura": atual.get("temperature_2m"),
        "sensacao": atual.get("apparent_temperature"),
        "chuva_prob": chuva,
    }


def previsao(latitude: float, longitude: float, *,
             cliente: httpx.Client | None = None) -> dict | None:
    """Temperatura, sensação térmica e probabilidade de chuva para agora.

    Devolve `None` se a API não responder — o chamador decide o que fazer, e a
    interface pede os dados ao usuário. É síncrona de propósito: a rota que a
    chama roda no threadpool do FastAPI, sem bloquear o laço de eventos.
    """
    chave = (round(latitude, 2), round(longitude, 2))
    agora = time.monotonic()
    with _trava:
        guardado = _cache.get(chave)
        if guardado and agora - guardado[0] < VALIDADE_CACHE:
            return dict(guardado[1])

    params = {
        "latitude": chave[0],
        "longitude": chave[1],
        "current": "temperature_2m,apparent_temperature,precipitation",
        "hourly": "precipitation_probability",
        "forecast_hours": HORAS_A_FRENTE,
        "timezone": "auto",
    }
    try:
        resposta = (cliente or _http()).get(URL, params=params)
        resposta.raise_for_status()
        resultado = _extrair(resposta.json())
    except Exception as exc:                     # noqa: BLE001 — degradar, não quebrar
        log.warning("Open-Meteo indisponível: %s", exc)
        return None

    if resultado["temperatura"] is None:
        log.warning("Open-Meteo respondeu sem temperatura")
        return None

    with _trava:
        if len(_cache) >= _LIMITE_CACHE:
            _cache.clear()
        _cache[chave] = (agora, resultado)
    return dict(resultado)
