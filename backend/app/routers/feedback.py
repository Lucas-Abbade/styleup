"""Rotas de feedback e personalização (seção 6.6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..erros import ErroAPI
from ..repositorio import Repositorio, com_consentimento
from ..schemas import FeedbackEntrada, FeedbackSaida
from ..services.recomendador import ajustar_pesos, normalizar_pesos

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackSaida)
def registrar(entrada: FeedbackEntrada, repo: Repositorio = Depends(com_consentimento)):
    """6.6.2 — registra a aprovação ou rejeição e reajusta os pesos do usuário.

    O ajuste acontece na mesma transação lógica do registro: se o feedback foi
    aceito, os pesos já mudaram para a próxima consulta. É o laço de
    realimentação da Figura 3.

    Repetir o mesmo voto não ensina de novo: sem isso, tocar três vezes em
    "gostei" valeria por três aprovações.
    """
    look = repo.obter_look(entrada.look_id)
    if not look:
        raise ErroAPI(404, "look_nao_encontrado", "Look não encontrado.")

    pesos = normalizar_pesos(repo.pesos())
    anterior = next((l.get("aprovado") for l in repo.listar_looks(salvos=False, limite=100)
                     if l["id"] == entrada.look_id), None)
    repo.registrar_feedback(entrada.look_id, entrada.aprovado)

    if anterior is entrada.aprovado:
        return {"registrado": True, "pesos": {k: round(v, 4) for k, v in pesos.items()}}

    novos = ajustar_pesos(pesos, look.get("parcelas") or {}, entrada.aprovado)
    repo.salvar_pesos(novos)
    return {"registrado": True, "pesos": novos}


@router.get("/metricas")
def metricas(repo: Repositorio = Depends(com_consentimento)):
    """Hit Rate@3 e Precision@3 do RNF04, calculados no banco, por usuário.

    Deixar isto exposto desde o início evita a correria de montar a avaliação na
    véspera da entrega.
    """
    return repo.metricas()
