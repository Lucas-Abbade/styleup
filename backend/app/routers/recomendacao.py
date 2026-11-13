"""Rotas de contexto e recomendação (seções 6.4 e 6.5)."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import Usuario, usuario_atual
from ..config import config
from ..db import como_usuario
from ..schemas import ContextoEntrada, RecomendacaoSaida
from ..services import clima as servico_clima
from ..services import explicacao, recomendador
from ..services.recomendador import Contexto, Peca, SemPecasSuficientes
from ..services.taxonomia import DRESS_CODE, POR_CHAVE

router = APIRouter(tags=["recomendação"])

JANELA_VARIEDADE = 10          # quantos looks recentes contam para a penalização


@router.get("/eventos")
def eventos():
    """6.4.1 — tipos de evento e a formalidade que cada um exige."""
    return [{"chave": k, **v} for k, v in DRESS_CODE.items()]


@router.post("/recomendacoes", response_model=RecomendacaoSaida)
async def recomendar(entrada: ContextoEntrada,
                     usuario: Usuario = Depends(usuario_atual)):
    """6.4 + 6.5 — monta o contexto, gera os três looks e os persiste.

    Persistir o look é o que torna o feedback possível: sem um identificador
    estável, o usuário não teria como dizer "gostei desse".
    """
    if entrada.evento not in DRESS_CODE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Evento desconhecido: {entrada.evento}")
    cliente = como_usuario(usuario)

    # ---------------------------------------------------------- 1. contexto
    temperatura, sensacao, chuva = entrada.temperatura, entrada.sensacao, entrada.chuva_prob
    clima_automatico = False
    if entrada.latitude is not None and entrada.longitude is not None:
        atual = await servico_clima.previsao(entrada.latitude, entrada.longitude)
        if atual:
            temperatura = atual["temperatura"]
            sensacao = atual["sensacao"]
            chuva = atual["chuva_prob"]
            clima_automatico = True

    contexto_linha = cliente.table("contextos").insert({
        "usuario_id": usuario.id,
        "evento": entrada.evento,
        "formalidade_alvo": DRESS_CODE[entrada.evento]["formalidade"],
        "temperatura": temperatura,
        "sensacao": sensacao,
        "chuva_prob": chuva,
        "latitude": entrada.latitude,
        "longitude": entrada.longitude,
    }).execute().data[0]

    ctx = Contexto(
        formalidade_alvo=contexto_linha["formalidade_alvo"],
        temperatura=temperatura,
        sensacao=sensacao,
        chuva_prob=chuva,
    )

    # ------------------------------------------------ 2. acervo e preferências
    linhas = (cliente.table("pecas").select("*")
              .eq("disponivel", True).execute().data)
    if not linhas:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Cadastre algumas peças antes de pedir uma recomendação.")

    usos = _usos_recentes(cliente)
    pecas = [
        Peca(
            id=l["id"], papel=l["papel"], categoria=l["categoria"],
            formalidade=l["formalidade"],
            cor_hsv=tuple(l["cor_hsv"]), neutra=l["neutra"],
            temp_min=l["temp_min"], temp_max=l["temp_max"],
            resiste_chuva=l["resiste_chuva"], disponivel=l["disponivel"],
            usos_recentes=usos.get(l["id"], 0),
        )
        for l in linhas
    ]

    prefs = (cliente.table("preferencias").select("pesos")
             .eq("usuario_id", usuario.id).execute().data)
    pesos = prefs[0]["pesos"] if prefs else recomendador.PESOS_PADRAO
    preferidas = _categorias_preferidas(cliente)

    # -------------------------------------------------------- 3. recomendação
    try:
        looks = recomendador.recomendar(pecas, ctx, pesos, preferidas)
    except SemPecasSuficientes as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Não há combinação possível para este contexto. Faltam peças "
            f"disponíveis em: {', '.join(exc.papeis)}."
        )

    # --------------------------------------------------------- 4. persistência
    por_id = {l["id"]: l for l in linhas}
    saida = []
    for posicao, look in enumerate(looks, start=1):
        texto = explicacao.explicar(look, ctx, entrada.evento, config.usar_llm)
        linha = cliente.table("looks").insert({
            "usuario_id": usuario.id,
            "contexto_id": contexto_linha["id"],
            "posicao": posicao,
            "score": round(look.score, 4),
            "parcelas": {k: round(v, 4) for k, v in look.parcelas.items()},
            "explicacao": texto,
        }).execute().data[0]

        cliente.table("look_pecas").insert([
            {"look_id": linha["id"], "peca_id": p.id, "papel": papel}
            for papel, p in look.pecas.items()
        ]).execute()

        saida.append({
            "id": linha["id"],
            "posicao": posicao,
            "score": round(look.score, 4),
            "parcelas": look.parcelas,
            "explicacao": texto,
            "pecas": [
                {
                    "id": p.id,
                    "codigo": por_id[p.id]["codigo"],
                    "papel": papel,
                    "categoria": p.categoria,
                    "rotulo": POR_CHAVE[p.categoria].rotulo if p.categoria in POR_CHAVE
                              else p.categoria,
                    "cor_nome": por_id[p.id]["cor_nome"],
                    "cor_hex": por_id[p.id]["cor_hex"],
                    "imagem_path": por_id[p.id].get("imagem_path"),
                }
                for papel, p in look.pecas.items()
            ],
        })

    return {
        "contexto": {
            "id": contexto_linha["id"],
            "evento": entrada.evento,
            "formalidade_alvo": ctx.formalidade_alvo,
            "temperatura": temperatura,
            "sensacao": sensacao,
            "chuva_prob": chuva,
            "clima_automatico": clima_automatico,
        },
        "looks": saida,
    }


# ------------------------------------------------------------------ apoio
def _usos_recentes(cliente) -> dict[str, int]:
    """Conta em quantos dos últimos looks cada peça apareceu."""
    recentes = (cliente.table("looks").select("id")
                .order("criado_em", desc=True)
                .limit(JANELA_VARIEDADE).execute().data)
    if not recentes:
        return {}
    ids = [l["id"] for l in recentes]
    vinculos = (cliente.table("look_pecas").select("peca_id")
                .in_("look_id", ids).execute().data)
    return dict(Counter(v["peca_id"] for v in vinculos))


def _categorias_preferidas(cliente) -> dict[str, float]:
    """Taxa de aprovação histórica por categoria, usada na nota de estilo.

    Uma categoria sem histórico vale 0.5 — nem premiada nem punida por ausência.
    """
    aprovados = (cliente.table("feedback").select("look_id, aprovado").execute().data)
    if not aprovados:
        return {}
    mapa = {f["look_id"]: f["aprovado"] for f in aprovados}
    vinculos = (cliente.table("look_pecas")
                .select("look_id, pecas(categoria)")
                .in_("look_id", list(mapa)).execute().data)

    contagem: dict[str, list[int]] = {}
    for v in vinculos:
        categoria = (v.get("pecas") or {}).get("categoria")
        if categoria:
            contagem.setdefault(categoria, []).append(1 if mapa[v["look_id"]] else 0)
    return {c: sum(vals) / len(vals) for c, vals in contagem.items()}
