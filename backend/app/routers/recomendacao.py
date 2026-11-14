"""Rotas de contexto e recomendação (seções 6.4 e 6.5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from ..config import config
from ..erros import ErroAPI
from ..repositorio import Repositorio, com_consentimento, localizacao_autorizada
from ..schemas import ContextoEntrada, RecomendacaoSaida, SalvarLookEntrada
from ..services import clima as servico_clima
from ..services import explicacao, recomendador
from ..services.interpretacao import interpretar
from ..services.recomendador import Contexto, Look, SemPecasSuficientes, taxa_suavizada
from ..services.taxonomia import (
    DRESS_CODE, ESTILOS, EVENTO_PADRAO, INSPIRACAO_POR_CHAVE, INSPIRACOES, POR_CHAVE,
)

router = APIRouter(tags=["recomendação"])

JANELA_VARIEDADE = 10          # quantos looks recentes contam para a penalização
CHUVA_PRESUMIDA = 0.8          # "vai chover", dito em texto livre

_NOME_PAPEL = {"superior": "parte de cima", "inferior": "parte de baixo",
               "calcado": "calçado"}


@router.get("/eventos")
def eventos():
    """6.4.1 — tipos de evento e a formalidade que cada um exige."""
    return [{"chave": k, "rotulo": v["rotulo"], "formalidade": v["formalidade"]}
            for k, v in DRESS_CODE.items()]


@router.get("/estilos")
def estilos():
    """Diretrizes de estilo aceitas em `estilo` (e reconhecidas no texto livre)."""
    return [{"chave": k, **v} for k, v in ESTILOS.items()]


@router.get("/inspiracoes")
def inspiracoes():
    """Atalhos da tela "Gerador de Looks": contextos pré-preenchidos."""
    return list(INSPIRACOES)


def _peca_do_look(papel: str, linha: dict) -> dict:
    cat = POR_CHAVE.get(linha["categoria"])
    return {
        "id": linha["id"], "codigo": linha["codigo"], "papel": papel,
        "categoria": linha["categoria"],
        "rotulo": cat.rotulo if cat else linha["categoria"],
        "cor_nome": linha["cor_nome"], "cor_hex": linha["cor_hex"],
        "imagem_path": linha.get("imagem_path"),
    }


def _resolver_pedido(entrada: ContextoEntrada) -> tuple[str, str | None, float | None,
                                                         bool, list[str]]:
    """Junta evento explícito, inspiração e texto livre num pedido só.

    Precedência: o que o usuário informou em campo próprio vence o atalho de
    inspiração, que vence o que foi deduzido do texto.
    """
    lido = interpretar(entrada.texto)
    atalho = INSPIRACAO_POR_CHAVE.get(entrada.inspiracao or "")
    if entrada.inspiracao and atalho is None:
        raise ErroAPI(400, "inspiracao_desconhecida",
                      f"Inspiração desconhecida: {entrada.inspiracao}")
    atalho = atalho or {}

    evento = entrada.evento or atalho.get("evento") or lido.evento or EVENTO_PADRAO
    if evento not in DRESS_CODE:
        raise ErroAPI(400, "evento_desconhecido", f"Evento desconhecido: {evento}")
    estilo = entrada.estilo or atalho.get("estilo") or lido.estilo
    if estilo and estilo not in ESTILOS:
        raise ErroAPI(400, "estilo_desconhecido", f"Estilo desconhecido: {estilo}")

    temperatura = atalho.get("temperatura", lido.temperatura)
    entendido = list(lido.entendido)
    if atalho:
        entendido.insert(0, atalho["rotulo"])
    return evento, estilo, temperatura, lido.chuva, entendido


@router.post("/recomendacoes", response_model=RecomendacaoSaida)
def recomendar(entrada: ContextoEntrada,
               repo: Repositorio = Depends(com_consentimento)):
    """6.4 + 6.5 — monta o contexto, gera os três looks e os persiste.

    Persistir o look é o que torna o feedback possível: sem um identificador
    estável, o usuário não teria como dizer "gostei desse".

    A rota é síncrona (roda no threadpool) e só grava no final, de uma vez: se
    não houver peças ou combinação, nada fica no banco — nem um contexto órfão
    que entraria na conta de `consultas` e derrubaria o Hit Rate@3.
    """
    evento, estilo, temp_pedida, chuva_pedida, entendido = _resolver_pedido(entrada)

    # ---------------------------------------------------------- 1. contexto
    temperatura, sensacao, chuva = entrada.temperatura, entrada.sensacao, entrada.chuva_prob
    clima_automatico = False
    if temperatura is None and temp_pedida is not None:
        temperatura = temp_pedida           # "dias frios", "32 graus": é um cenário
    elif (temperatura is None and entrada.latitude is not None
          and entrada.longitude is not None and localizacao_autorizada(repo)):
        atual = servico_clima.previsao(entrada.latitude, entrada.longitude)
        if atual:
            temperatura = atual["temperatura"]
            sensacao = atual["sensacao"]
            chuva = atual["chuva_prob"] if chuva is None else chuva
            clima_automatico = True
    if chuva is None and chuva_pedida:
        chuva = CHUVA_PRESUMIDA

    ctx = Contexto(
        formalidade_alvo=DRESS_CODE[evento]["formalidade"],
        temperatura=temperatura, sensacao=sensacao, chuva_prob=chuva,
        evento=evento, estilo=estilo,
    )

    # ------------------------------------------------ 2. acervo e preferências
    linhas = repo.listar_pecas(disponivel=True)
    if not linhas:
        raise ErroAPI(409, "guarda_roupa_vazio",
                      "Cadastre algumas peças antes de pedir uma recomendação.")

    usos = repo.usos_recentes(JANELA_VARIEDADE)
    pecas = [p for p in (recomendador.peca_de_linha(l, usos.get(l["id"], 0))
                         for l in linhas) if p is not None]
    pesos = recomendador.normalizar_pesos(repo.pesos())
    preferidas = {categoria: taxa_suavizada(aprovados, total)
                  for categoria, (aprovados, total)
                  in repo.aprovacao_por_categoria(config.janela_feedback).items()}

    # -------------------------------------------------------- 3. recomendação
    try:
        resultado = recomendador.recomendar_com_avisos(pecas, ctx, pesos, preferidas)
    except SemPecasSuficientes as exc:
        nomes = [_NOME_PAPEL.get(p, p) for p in exc.papeis]
        raise ErroAPI(
            409, "sem_combinacao",
            "Ainda não dá para montar um look: falta cadastrar "
            f"{' e '.join(nomes)}.", faltando=exc.papeis)

    # --------------------------------------------------------- 4. persistência
    por_id = {l["id"]: l for l in linhas}
    contexto_id = str(uuid.uuid4())
    registros, saida = [], []
    for posicao, look in enumerate(resultado.looks, start=1):
        item = _montar(look, ctx, evento, posicao, por_id)
        registros.append(item["registro"])
        saida.append(item["saida"])

    repo.registrar_recomendacao({
        "id": contexto_id, "evento": evento, "estilo": estilo,
        "formalidade_alvo": ctx.formalidade_alvo,
        "temperatura": temperatura, "sensacao": sensacao, "chuva_prob": chuva,
    }, registros)

    return {
        "contexto": {
            "id": contexto_id,
            "evento": evento,
            "evento_rotulo": DRESS_CODE[evento]["rotulo"],
            "estilo": estilo,
            "formalidade_alvo": ctx.formalidade_alvo,
            "temperatura": temperatura,
            "sensacao": sensacao,
            "chuva_prob": chuva,
            "clima_automatico": clima_automatico,
            "entendido": entendido,
        },
        "looks": saida,
        "avisos": resultado.avisos,
    }


def _montar(look: Look, ctx: Contexto, evento: str, posicao: int,
            por_id: dict[str, dict]) -> dict:
    look_id = str(uuid.uuid4())
    texto = explicacao.explicar(look, ctx, evento, config.usar_llm)
    titulo = explicacao.titulo(look, ctx)
    resumo = explicacao.resumo(look, ctx)
    parcelas = {k: round(v, 4) for k, v in look.parcelas.items()}
    return {
        "registro": {
            "id": look_id, "posicao": posicao, "score": round(look.score, 4),
            "parcelas": parcelas, "titulo": titulo, "resumo": resumo,
            "explicacao": texto,
            "pecas": [{"peca_id": p.id, "papel": papel} for papel, p in look.todas],
        },
        "saida": {
            "id": look_id, "posicao": posicao, "score": round(look.score, 4),
            "parcelas": parcelas, "titulo": titulo, "resumo": resumo,
            "explicacao": texto, "salvo": False, "aprovado": None,
            "pecas": [_peca_do_look(papel, por_id[p.id]) for papel, p in look.todas],
        },
    }


# --------------------------------------------------------------- histórico
_ORDEM_PAPEL = {"sobreposicao": 0, "superior": 1, "inferior": 2, "calcado": 3,
                "acessorio": 4}


@router.get("/looks")
def listar_looks(salvos: bool = False, limite: int = 30,
                 repo: Repositorio = Depends(com_consentimento)):
    """Looks já gerados; com `salvos=true`, só os que o usuário guardou."""
    limite = max(1, min(limite, 100))
    saida = []
    for l in repo.listar_looks(salvos=salvos, limite=limite):
        pecas = sorted(l.get("pecas", []), key=lambda v: _ORDEM_PAPEL.get(v["papel"], 9))
        saida.append({
            "id": l["id"], "posicao": l["posicao"], "score": l["score"],
            "parcelas": l.get("parcelas") or {}, "titulo": l.get("titulo") or "",
            "resumo": l.get("resumo") or "", "explicacao": l.get("explicacao") or "",
            "salvo": bool(l.get("salvo")), "aprovado": l.get("aprovado"),
            "evento": l.get("evento"), "criado_em": l.get("criado_em"),
            "pecas": [_peca_do_look(v["papel"], v["peca"]) for v in pecas],
        })
    return saida


@router.put("/looks/{look_id}/salvo")
def salvar_look(look_id: str, entrada: SalvarLookEntrada,
                repo: Repositorio = Depends(com_consentimento)):
    """Guarda (ou tira) um look da lista de salvos do usuário."""
    if not repo.marcar_look_salvo(look_id, entrada.salvo):
        raise ErroAPI(404, "look_nao_encontrado", "Look não encontrado.")
    return {"id": look_id, "salvo": entrada.salvo}
