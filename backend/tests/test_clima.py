"""Integração com a Open-Meteo, com transporte HTTP simulado (sem rede)."""

from __future__ import annotations

import httpx

from app.services import clima

RESPOSTA = {
    "current": {"time": "2026-11-14T15:00", "temperature_2m": 34.2,
                "apparent_temperature": 37.9, "precipitation": 0.0},
    "hourly": {"time": ["2026-11-14T15:00", "2026-11-14T16:00", "2026-11-14T17:00"],
               "precipitation_probability": [10, 65, None]},
}


def _cliente(resposta=RESPOSTA, status=200, registro=None):
    def tratar(requisicao: httpx.Request) -> httpx.Response:
        if registro is not None:
            registro.append(requisicao)
        return httpx.Response(status, json=resposta)
    return httpx.Client(transport=httpx.MockTransport(tratar))


def test_chuva_vem_da_serie_horaria_e_usa_o_pior_caso():
    """Fase 2, item 11: a probabilidade é pedida em `hourly` (campo documentado),
    e vale o máximo das próximas horas — quem sai agora fica um tempo na rua."""
    registro = []
    resultado = clima.previsao(-15.6, -56.1, cliente=_cliente(registro=registro))
    assert resultado == {"temperatura": 34.2, "sensacao": 37.9, "chuva_prob": 0.65}
    params = dict(registro[0].url.params)
    assert params["hourly"] == "precipitation_probability"
    assert "precipitation_probability" not in params["current"]
    assert params["forecast_hours"] == "3" and params["timezone"] == "auto"


def test_cache_por_local_evita_segunda_chamada():
    """Fase 3, item 2: ~2 s da recomendação vinham desta consulta."""
    registro = []
    cliente = _cliente(registro=registro)
    primeiro = clima.previsao(-15.6012, -56.0974, cliente=cliente)
    segundo = clima.previsao(-15.5989, -56.1021, cliente=cliente)   # mesmo ~km
    assert primeiro == segundo and len(registro) == 1
    clima.previsao(-23.55, -46.63, cliente=cliente)                 # outra cidade
    assert len(registro) == 2


def test_cache_expira(monkeypatch):
    registro = []
    cliente = _cliente(registro=registro)
    relogio = [1000.0]
    monkeypatch.setattr(clima.time, "monotonic", lambda: relogio[0])
    clima.previsao(1, 1, cliente=cliente)
    relogio[0] += clima.VALIDADE_CACHE + 1
    clima.previsao(1, 1, cliente=cliente)
    assert len(registro) == 2


def test_coordenada_sai_arredondada():
    """LGPD (necessidade): a Open-Meteo recebe a posição com ~1 km de precisão."""
    registro = []
    clima.previsao(-15.601234, -56.097456, cliente=_cliente(registro=registro))
    params = dict(registro[0].url.params)
    assert params["latitude"] == "-15.6" and params["longitude"] == "-56.1"


def test_falhas_degradam_para_none_e_nao_entram_no_cache():
    registro = []
    assert clima.previsao(2, 2, cliente=_cliente({"error": True, "reason": "x"}, 400, registro)) is None
    assert clima.previsao(2, 2, cliente=_cliente({}, 200, registro)) is None   # sem temperatura

    def cair(_):
        raise httpx.ConnectError("sem internet")
    assert clima.previsao(2, 2, cliente=httpx.Client(transport=httpx.MockTransport(cair))) is None
    assert clima.previsao(2, 2, cliente=_cliente(registro=registro))["temperatura"] == 34.2
    assert len(registro) == 3


def test_sem_previsao_horaria_mas_chovendo_agora():
    resposta = {"current": {"temperature_2m": 22, "apparent_temperature": 22, "precipitation": 1.4},
                "hourly": {"precipitation_probability": [None]}}
    assert clima.previsao(3, 3, cliente=_cliente(resposta))["chuva_prob"] == 1.0
    seco = {"current": {"temperature_2m": 22, "apparent_temperature": 22, "precipitation": 0}}
    assert clima.previsao(4, 4, cliente=_cliente(seco))["chuva_prob"] is None
