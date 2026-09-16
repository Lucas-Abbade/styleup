"""Rotas de contexto e recomendação (seções 6.4 e 6.5).

Esta é a funcionalidade principal do produto. O caminho é sempre o mesmo:
monta o contexto → carrega o acervo → recomenda → persiste → responde. Cada
etapa que pode falhar por causa dos dados do usuário (acervo vazio, nenhuma
combinação viável) devolve 409 com mensagem em português; nada aqui produz 500.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import config
from ..db import obter_repositorio
from ..repositorio import Repositorio
from ..schemas import ContextoEntrada, RecomendacaoSaida
from ..services import clima as servico_clima
from ..services import explicacao, recomendador
from ..services.recomendador import Contexto, Peca, SemPecasSuficientes
from ..services.taxonomia import DRESS_CODE, POR_CHAVE

log = logging.getLogger(__name__)
# O Starlette renomeou HTTP_422_UNPROCESSABLE_ENTITY; o numero e estavel.
HTTP_422 = 422

router = APIRouter(tags=["recomendação"])

PAPEIS_EM_PORTUGUES = {
    "superior": "parte de cima",
    "inferior": "parte de baixo",
    "calcado": "calçado",
    "sobreposicao": "sobreposição",
}


@router.get("/eventos")
def eventos():
    """6.4.1 — tipos de evento e a formalidade que cada um exige."""
    return [{"chave": k, **v} for k, v in DRESS_CODE.items()]


@router.post("/recomendacoes", response_model=RecomendacaoSaida)
async def recomendar(entrada: ContextoEntrada,
                     repo: Repositorio = Depends(obter_repositorio)):
    """6.4 + 6.5 — monta o contexto, gera os três looks e os persiste.

    Persistir o look é o que torna o feedback possível: sem um identificador
    estável, o usuário não teria como dizer "gostei desse".
    """
    if entrada.evento not in DRESS_CODE:
        raise HTTPException(
            HTTP_422,
            f"Evento desconhecido: {entrada.evento}. "
            f"Use um destes: {', '.join(DRESS_CODE)}.")

    # ------------------------------------------------------ 1. acervo primeiro
    # Carregar as peças antes de gravar o contexto evita registrar consultas que
    # nunca produziram look, o que distorceria o Hit Rate@3 do RNF04.
    linhas = repo.listar_pecas(disponivel=True)
    if not linhas:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Seu guarda-roupa está vazio. Cadastre ao menos uma parte de cima, "
            "uma parte de baixo e um calçado para receber sugestões.")

    # ---------------------------------------------------------- 2. contexto
    temperatura, sensacao, chuva = entrada.temperatura, entrada.sensacao, entrada.chuva_prob
    clima_automatico = False
    if entrada.latitude is not None and entrada.longitude is not None:
        atual = await servico_clima.previsao(entrada.latitude, entrada.longitude)
        if atual:
            temperatura = atual["temperatura"]
            sensacao = atual["sensacao"]
            chuva = atual["chuva_prob"]
            clima_automatico = True
        else:
            log.info("Clima indisponível; seguindo com o contexto informado.")

    ctx = Contexto(
        formalidade_alvo=DRESS_CODE[entrada.evento]["formalidade"],
        temperatura=temperatura,
        sensacao=sensacao,
        chuva_prob=chuva,
    )

    # -------------------------------------------------- 3. peças e preferências
    usos = repo.usos_recentes()
    pecas: list[Peca] = []
    for l in linhas:
        try:
            pecas.append(Peca(
                id=l["id"], papel=l["papel"], categoria=l["categoria"],
                formalidade=int(l["formalidade"]),
                cor_hsv=tuple(float(v) for v in l["cor_hsv"]),
                neutra=bool(l["neutra"]),
                cor_nome=str(l.get("cor_nome") or ""),
                temp_min=float(l["temp_min"]), temp_max=float(l["temp_max"]),
                resiste_chuva=bool(l["resiste_chuva"]),
                disponivel=bool(l["disponivel"]),
                usos_recentes=usos.get(l["id"], 0),
            ))
        except (KeyError, TypeError, ValueError) as exc:
            # uma peça corrompida não pode derrubar a recomendação inteira
            log.warning("Peça %s ignorada por dados inconsistentes: %s",
                        l.get("codigo", l.get("id")), exc)

    if not pecas:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Nenhuma peça do seu guarda-roupa pôde ser usada. Revise o cadastro "
            "das peças e tente novamente.")

    pesos = repo.obter_pesos() or recomendador.PESOS_PADRAO
    preferidas = repo.taxa_por_categoria()

    # ------------------------------------------------------- 4. recomendação
    try:
        looks = recomendador.recomendar(pecas, ctx, pesos, preferidas)
    except SemPecasSuficientes as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, _mensagem_sem_pecas(exc, ctx))

    # ------------------------------------------------------- 5. persistência
    contexto_linha = repo.criar_contexto({
        "evento": entrada.evento,
        "formalidade_alvo": ctx.formalidade_alvo,
        "temperatura": temperatura,
        "sensacao": sensacao,
        "chuva_prob": chuva,
        "latitude": entrada.latitude,
        "longitude": entrada.longitude,
    })

    a_salvar = []
    for posicao, look in enumerate(looks, start=1):
        a_salvar.append({
            "posicao": posicao,
            "score": round(look.score, 4),
            "parcelas": {k: round(v, 4) for k, v in look.parcelas.items()},
            "explicacao": explicacao.explicar(look, ctx, entrada.evento, config.usar_llm),
            "pecas": {papel: p.id for papel, p in look.pecas.items()},
        })
    salvos = repo.salvar_looks(contexto_linha["id"], a_salvar)

    # ------------------------------------------------------------ 6. resposta
    por_id = {l["id"]: l for l in linhas}
    return {
        "contexto": {
            "id": contexto_linha["id"],
            "evento": entrada.evento,
            "rotulo_evento": DRESS_CODE[entrada.evento]["rotulo"],
            "formalidade_alvo": ctx.formalidade_alvo,
            "temperatura": temperatura,
            "sensacao": sensacao,
            "chuva_prob": chuva,
            "clima_automatico": clima_automatico,
        },
        "looks": [
            {
                "id": salvo["id"],
                "posicao": salvo["posicao"],
                "score": salvo["score"],
                "parcelas": salvo["parcelas"],
                "explicacao": salvo["explicacao"],
                "pecas": [
                    _peca_do_look(papel, peca, por_id)
                    for papel, peca in look.pecas.items()
                ],
            }
            for salvo, look in zip(salvos, looks)
        ],
    }


# ------------------------------------------------------------------ apoio
def _peca_do_look(papel: str, peca: Peca, por_id: dict) -> dict:
    linha = por_id[peca.id]
    return {
        "id": peca.id,
        "codigo": linha["codigo"],
        "papel": papel,
        "categoria": peca.categoria,
        "rotulo": POR_CHAVE[peca.categoria].rotulo
                  if peca.categoria in POR_CHAVE else peca.categoria,
        "cor_nome": linha["cor_nome"],
        "cor_hex": linha["cor_hex"],
        "imagem_path": linha.get("imagem_path"),
    }


def _mensagem_sem_pecas(exc: SemPecasSuficientes, ctx: Contexto) -> str:
    """Explica *por que* nenhuma combinação foi possível.

    "Faltam peças" não ajuda ninguém. O usuário pode ter dez camisetas e nenhuma
    servir para 8 °C, e o texto precisa dizer isso para que ele saiba se cadastra
    uma peça nova ou escolhe outro compromisso.
    """
    papeis = ", ".join(PAPEIS_EM_PORTUGUES.get(p, p) for p in exc.papeis)
    motivos = [f"não há peça disponível de {papeis} para este contexto"]

    temp = ctx.temperatura_efetiva
    if temp is not None:
        motivos.append(f"a temperatura considerada foi de {temp:.0f} °C")
    if ctx.vai_chover:
        motivos.append("a previsão de chuva descarta calçados abertos")
    motivos.append(f"o compromisso pede formalidade {ctx.formalidade_alvo} de 5")

    return (". ".join(m.capitalize() if i == 0 else m
                      for i, m in enumerate(motivos))
            + ". Marque outras peças como disponíveis, cadastre uma peça que "
              "sirva, ou escolha outro compromisso.")
