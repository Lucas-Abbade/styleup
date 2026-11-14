"""Camada de explicação (módulo M6).

O modo padrão é o baseado em template: determinístico, gratuito, sempre
disponível — é o que o RNF14 exige. O modo com LLM é um enfeite opcional que
melhora a fluência do texto e nunca é caminho crítico: se a chave não existir ou
a chamada falhar, o template assume sem o usuário perceber.
"""

from __future__ import annotations

import logging

from .cor import TERROSAS, concordar, nomear
from .recomendador import (
    ESTILO_ATENDIDO, LIMIAR_SOBREPOSICAO, Contexto, Look, Peca, _familias_de_matiz,
    cor_efetiva, nota_estilo_pedido,
)
from .taxonomia import DRESS_CODE, ESTILOS, NIVEL_FORMALIDADE, POR_CHAVE

log = logging.getLogger(__name__)


def _nome_da_cor(peca: Peca) -> str:
    """O nome que está no banco — o mesmo do chip da interface.

    Recalcular a partir do HSV fazia o texto discordar do chip quando o usuário
    corrigia a cor. O cálculo só vale para peças sem nome gravado.
    """
    return peca.cor_nome or nomear(*peca.cor_hsv)[0]


def _descrever(peca: Peca) -> str:
    cat = POR_CHAVE.get(peca.categoria)
    rotulo = cat.rotulo.lower() if cat else peca.categoria.replace("-", " ")
    return f"{rotulo} {concordar(_nome_da_cor(peca), cat.genero if cat else 'm')}"


def _enumerar(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + f" e {itens[-1]}"


def paleta(look: Look) -> str:
    """Classifica a paleta do look. Devolve uma chave de `_PALETAS`."""
    pecas = list(look.pecas.values())
    efetivas = [cor_efetiva(p) for p in pecas]
    coloridas = [cor for cor, neutra in efetivas if not neutra]
    nomes = [_nome_da_cor(p) for p in pecas]

    if all(n in ("preto", "grafite") for n in nomes):
        return "all-black"
    if sum(n in TERROSAS for n in nomes) >= max(2, len(nomes) - 1):
        return "terroso"
    if not coloridas:
        return "neutro"
    if len(coloridas) == 1:
        return "ponto-de-cor"
    return "tonal" if _familias_de_matiz(coloridas) == 1 else "colorido"


# chave -> (etiqueta curta para o título, expressão para o meio de uma frase)
_PALETAS = {
    "all-black": ("All black", "preto dos pés à cabeça"),
    "terroso": ("Tons terrosos", "tons terrosos"),
    "neutro": ("Neutros", "tons neutros"),
    "ponto-de-cor": ("Ponto de cor", "tons neutros com um ponto de cor"),
    "tonal": ("Tom sobre tom", "tom sobre tom"),
    "colorido": ("Colorido", "cores que conversam entre si"),
}


def _estilo_atendido(look: Look, ctx: Contexto) -> bool:
    return (ctx.estilo in ESTILOS
            and nota_estilo_pedido(look, ctx.estilo) >= ESTILO_ATENDIDO)


def titulo(look: Look, ctx: Contexto) -> str:
    """Etiqueta curta do look, como "Casual • Tons terrosos".

    O estilo pedido só vai para o título quando o look de fato o atende: chamar
    de "All black" uma combinação com calça azul seria prometer o que não há.
    """
    valores = [p.formalidade for p in look.pecas.values()]
    nivel = NIVEL_FORMALIDADE[min(5, max(1, round(sum(valores) / len(valores))))]
    segundo = (ESTILOS[ctx.estilo]["rotulo"] if _estilo_atendido(look, ctx)
               else _PALETAS[paleta(look)][0])
    return f"{nivel} • {segundo}"


def por_template(look: Look, ctx: Contexto, evento: str | None = None) -> str:
    """Monta a justificativa a partir das parcelas que mais pesaram no score.

    Explicar *tudo* vira ruído. Citamos o clima quando ele existe, a formalidade
    quando o evento foi informado, e a cor apenas quando a harmonia foi de fato
    boa — elogiar uma combinação medíocre destrói a confiança na explicação.
    """
    partes: list[str] = []

    itens = [_descrever(p) for papel, p in look.pecas.items()
             if papel in ("superior", "inferior", "calcado")]
    partes.append("Combinação de " + _enumerar(itens))

    tem_sobreposicao = "sobreposicao" in look.pecas
    if tem_sobreposicao:
        partes.append(f"com {_descrever(look.pecas['sobreposicao'])} por cima")

    temp = ctx.temperatura_efetiva
    if temp is not None:
        # mesmo limiar do motor: abaixo dele o look pede (e, se existir, traz) agasalho
        if temp < LIMIAR_SOBREPOSICAO and tem_sobreposicao:
            partes.append(f"adequada aos {temp:.0f} °C previstos, que pedem agasalho")
        elif temp < LIMIAR_SOBREPOSICAO:
            partes.append(f"a opção mais quente do guarda-roupa para os {temp:.0f} °C "
                          "previstos — vale levar um agasalho, porque não há "
                          "sobreposição cadastrada")
        elif temp > 28:
            partes.append(f"leve para os {temp:.0f} °C previstos")
        else:
            partes.append(f"confortável para os {temp:.0f} °C previstos")

    if ctx.vai_chover:
        partes.append("com calçado fechado por causa da chuva")

    if evento:
        rotulo = DRESS_CODE.get(evento, {}).get("rotulo", evento)
        partes.append(f"no nível de formalidade esperado para {rotulo.lower()}")

    if _estilo_atendido(look, ctx):
        partes.append(f"na linha {ESTILOS[ctx.estilo]['rotulo'].lower()} que você pediu")

    if look.parcelas.get("cor", 0) >= 0.8:
        partes.append("e com cores que se harmonizam")

    texto = partes[0] + (", " + ", ".join(partes[1:]) if len(partes) > 1 else "") + "."
    if look.acessorios:
        texto += " Para completar: " + _enumerar([_descrever(a) for a in look.acessorios]) + "."
    return texto


def resumo(look: Look, ctx: Contexto) -> str:
    """Uma linha para a tela do look: o porquê, sem repetir a lista de peças."""
    cor = _PALETAS[paleta(look)][1]
    if _estilo_atendido(look, ctx) and ctx.estilo != "all-black":
        inicio = f"Look {ESTILOS[ctx.estilo]['rotulo'].lower()} em {cor}"
    else:
        inicio = f"Combinação em {cor}"
    temp = ctx.temperatura_efetiva
    if temp is None:
        clima = "pensada para a ocasião"
    elif temp < LIMIAR_SOBREPOSICAO:
        clima = f"que segura os {temp:.0f} °C"
    elif temp > 28:
        clima = f"leve para os {temp:.0f} °C"
    else:
        clima = f"confortável para os {temp:.0f} °C"
    return f"{inicio}, {clima}."


def explicar(look: Look, ctx: Contexto, evento: str | None = None,
             usar_llm: bool = False) -> str:
    texto = por_template(look, ctx, evento)
    if not usar_llm:
        return texto
    try:
        return _por_llm(texto)
    except Exception as exc:                     # noqa: BLE001 — fallback é o objetivo
        log.warning("LLM indisponível, usando template: %s", exc)
        return texto


def _por_llm(base: str) -> str:
    """Reescreve a explicação em tom mais natural. Opcional por definição.

    Implementar apenas se sobrar tempo no cronograma. A assinatura já está aqui
    para que o resto do sistema não precise mudar quando isso acontecer.
    """
    raise NotImplementedError(
        "Modo LLM não implementado; o template atende ao RNF14."
    )
