"""Integração com a API de clima (módulo M4).

Open-Meteo não exige chave nem cadastro, o que atende ao RNF14 (nenhuma
dependência paga obrigatória). A falha da API não pode derrubar a recomendação:
o RNF07 manda cair para contexto informado manualmente, então aqui devolvemos
`None` em vez de propagar exceção.
"""

from __future__ import annotations

import logging

import httpx

log = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 4.0            # a recomendação tem orçamento de 3 s (RNF02); não dá para esperar


async def previsao(latitude: float, longitude: float) -> dict | None:
    """Temperatura, sensação térmica e probabilidade de chuva para agora.

    Devolve `None` se a API não responder — o chamador decide o que fazer, e a
    interface pede os dados ao usuário.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,precipitation_probability",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            resposta = await cliente.get(URL, params=params)
            resposta.raise_for_status()
            atual = resposta.json()["current"]
    except Exception as exc:                     # noqa: BLE001 — degradar, não quebrar
        log.warning("Open-Meteo indisponível: %s", exc)
        return None

    prob = atual.get("precipitation_probability")
    return {
        "temperatura": atual.get("temperature_2m"),
        "sensacao": atual.get("apparent_temperature"),
        "chuva_prob": (prob / 100) if prob is not None else None,
    }
