"""Rotas de feedback e personalização (seção 6.6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import Usuario, usuario_atual
from ..db import como_usuario
from ..schemas import FeedbackEntrada, FeedbackSaida
from ..services.recomendador import PESOS_PADRAO, ajustar_pesos

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackSaida)
def registrar(entrada: FeedbackEntrada, usuario: Usuario = Depends(usuario_atual)):
    """6.6.2 — registra a aprovação ou rejeição e reajusta os pesos do usuário.

    O ajuste acontece na mesma transação lógica do registro: se o feedback foi
    aceito, os pesos já mudaram para a próxima consulta. É o laço de
    realimentação da Figura 3.
    """
    cliente = como_usuario(usuario)

    look = (cliente.table("looks").select("parcelas")
            .eq("id", entrada.look_id).execute().data)
    if not look:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Look não encontrado.")

    cliente.table("feedback").upsert({
        "usuario_id": usuario.id,
        "look_id": entrada.look_id,
        "aprovado": entrada.aprovado,
    }, on_conflict="usuario_id,look_id").execute()

    atuais = (cliente.table("preferencias").select("pesos")
              .eq("usuario_id", usuario.id).execute().data)
    pesos = atuais[0]["pesos"] if atuais else dict(PESOS_PADRAO)

    novos = ajustar_pesos(pesos, look[0]["parcelas"] or {}, entrada.aprovado)
    cliente.table("preferencias").upsert({
        "usuario_id": usuario.id, "pesos": novos,
    }, on_conflict="usuario_id").execute()

    return {"registrado": True, "pesos": novos}


@router.get("/metricas")
def metricas(usuario: Usuario = Depends(usuario_atual)):
    """Hit Rate@3 e Precision@3 do RNF04, calculados no banco.

    Deixar isto exposto desde o início evita a correria de montar a avaliação na
    véspera da entrega.
    """
    dados = como_usuario(usuario).table("metricas_recomendacao").select("*").execute().data
    return dados[0] if dados else {
        "consultas": 0, "looks_aprovados": 0, "hit_rate_3": None, "precision_3": None,
    }
