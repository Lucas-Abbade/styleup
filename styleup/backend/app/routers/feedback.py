"""Rotas de feedback e personalização (seção 6.6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..db import obter_repositorio
from ..repositorio import Repositorio
from ..schemas import FeedbackEntrada, FeedbackSaida
from ..services.recomendador import PESOS_PADRAO, ajustar_pesos

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackSaida)
def registrar(entrada: FeedbackEntrada, repo: Repositorio = Depends(obter_repositorio)):
    """6.6.2 — registra a aprovação ou rejeição e reajusta os pesos do usuário.

    O ajuste acontece junto do registro: se o feedback foi aceito, os pesos já
    valem para a próxima consulta. É o laço de realimentação da Figura 3.
    """
    parcelas = repo.parcelas_do_look(entrada.look_id)
    if parcelas is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Look não encontrado.")

    repo.registrar_feedback(entrada.look_id, entrada.aprovado)

    pesos = repo.obter_pesos() or dict(PESOS_PADRAO)
    novos = ajustar_pesos(pesos, parcelas, entrada.aprovado)
    repo.salvar_pesos(novos)

    return {"registrado": True, "pesos": novos}


@router.get("/metricas")
def metricas(repo: Repositorio = Depends(obter_repositorio)):
    """Hit Rate@3 e Precision@3 do RNF04.

    Expor isto desde o início evita montar a avaliação na véspera da entrega.
    """
    return repo.metricas()
