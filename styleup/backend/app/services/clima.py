"""Integração com a API de clima (módulo M4).

Open-Meteo não exige chave nem cadastro, o que atende ao RNF14 (nenhuma
dependência paga obrigatória). A falha da API não pode derrubar a recomendação:
o RNF07 manda cair para contexto informado manualmente, então devolvemos `None`
em vez de propagar exceção.

Duas otimizações que valem o código extra:

* **Cliente HTTP compartilhado.** A versão anterior criava um `AsyncClient` por
  chamada, e cada um pagava DNS e handshake TLS do zero — dezenas de
  milissegundos dentro do orçamento de 3 s do RNF02.
* **Cache com validade.** Previsão do tempo não muda em dez minutos, e todos os
  usuários de um mesmo bairro caem na mesma célula de 0,01° (~1 km). Numa
  demonstração com a turma inteira na mesma sala, a segunda consulta em diante
  não sai da máquina.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

log = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 4.0            # a recomendação tem orçamento de 3 s (RNF02)
VALIDADE_CACHE = 600     # 10 minutos
PRECISAO_CELULA = 2      # casas decimais no arredondamento da coordenada
MAX_CACHE = 256

_cliente: httpx.AsyncClient | None = None
_trava = asyncio.Lock()
# chave -> (instante da coleta, previsão)
_cache: dict[tuple[float, float], tuple[float, dict]] = {}


async def _obter_cliente() -> httpx.AsyncClient:
    global _cliente
    if _cliente is None or _cliente.is_closed:
        async with _trava:
            if _cliente is None or _cliente.is_closed:
                _cliente = httpx.AsyncClient(
                    timeout=TIMEOUT,
                    limits=httpx.Limits(max_keepalive_connections=5,
                                        max_connections=10),
                    headers={"User-Agent": "StyleUp/0.2 (projeto academico)"},
                )
    return _cliente


async def fechar_cliente() -> None:
    """Encerra o cliente no shutdown da aplicação, sem deixar socket pendurado."""
    global _cliente
    if _cliente is not None and not _cliente.is_closed:
        await _cliente.aclose()
    _cliente = None


def limpar_cache() -> None:
    _cache.clear()


def _celula(latitude: float, longitude: float) -> tuple[float, float]:
    return (round(latitude, PRECISAO_CELULA), round(longitude, PRECISAO_CELULA))


async def previsao(latitude: float, longitude: float) -> dict | None:
    """Temperatura, sensação térmica e probabilidade de chuva para agora.

    Devolve `None` se a API não responder — o chamador decide o que fazer, e a
    interface pede os dados ao usuário.
    """
    chave = _celula(latitude, longitude)
    agora = time.monotonic()

    guardado = _cache.get(chave)
    if guardado and (agora - guardado[0]) < VALIDADE_CACHE:
        return guardado[1]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,precipitation_probability",
        "timezone": "auto",
    }
    try:
        cliente = await _obter_cliente()
        resposta = await cliente.get(URL, params=params)
        resposta.raise_for_status()
        atual = resposta.json()["current"]
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        # Degradar em vez de quebrar é exigência do RNF07 — mas o nível do log
        # separa as duas causas. Falha de rede é rotina (warning); resposta em
        # formato inesperado é defeito nosso ou mudança na API externa, e vai com
        # traceback (exception) para não passar por instabilidade de rede.
        if isinstance(exc, httpx.HTTPError):
            log.warning("Open-Meteo indisponível: %s", exc)
        else:
            log.exception("Resposta inesperada da Open-Meteo: %s", exc)
        # Preferimos um dado de até 10 min atrás a nenhum dado: se o cache tem
        # uma leitura vencida para esta célula, ela ainda descreve o clima melhor
        # do que ignorar a estação do ano.
        if guardado:
            log.info("Usando previsão em cache, coletada há %.0f s",
                     agora - guardado[0])
            return guardado[1]
        return None

    prob = atual.get("precipitation_probability")
    resultado = {
        "temperatura": atual.get("temperature_2m"),
        "sensacao": atual.get("apparent_temperature"),
        "chuva_prob": (prob / 100) if prob is not None else None,
    }

    if len(_cache) >= MAX_CACHE:
        # descarta a entrada mais antiga; o volume aqui é pequeno por natureza
        mais_antiga = min(_cache, key=lambda k: _cache[k][0])
        _cache.pop(mais_antiga, None)
    _cache[chave] = (agora, resultado)
    return resultado
