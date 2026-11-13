"""Camada de explicação (módulo M6).

O modo padrão é o baseado em template: determinístico, gratuito, sempre
disponível — é o que o RNF14 exige. O modo com LLM é um enfeite opcional que
melhora a fluência do texto e nunca é caminho crítico: se a chave não existir ou
a chamada falhar, o template assume sem o usuário perceber.
"""

from __future__ import annotations

import logging

from .cor import concordar, nomear
from .recomendador import Contexto, Look
from .taxonomia import DRESS_CODE, POR_CHAVE

log = logging.getLogger(__name__)


def _descrever(peca) -> str:
    cat = POR_CHAVE.get(peca.categoria)
    rotulo = cat.rotulo.lower() if cat else peca.categoria.replace("-", " ")
    nome_cor, _ = nomear(*peca.cor_hsv)
    return f"{rotulo} {concordar(nome_cor, cat.genero if cat else 'm')}"


def por_template(look: Look, ctx: Contexto, evento: str | None = None) -> str:
    """Monta a justificativa a partir das parcelas que mais pesaram no score.

    Explicar *tudo* vira ruído. Citamos o clima quando ele existe, a formalidade
    quando o evento foi informado, e a cor apenas quando a harmonia foi de fato
    boa — elogiar uma combinação medíocre destrói a confiança na explicação.
    """
    partes: list[str] = []

    itens = [_descrever(p) for papel, p in look.pecas.items()
             if papel in ("superior", "inferior", "calcado")]
    partes.append("Combinação de " + ", ".join(itens[:-1]) + f" e {itens[-1]}")

    if "sobreposicao" in look.pecas:
        partes.append(f"com {_descrever(look.pecas['sobreposicao'])} por cima")

    temp = ctx.temperatura_efetiva
    if temp is not None:
        if temp < 15:
            partes.append(f"adequada aos {temp:.0f} °C previstos, que pedem agasalho")
        elif temp > 28:
            partes.append(f"leve para os {temp:.0f} °C previstos")
        else:
            partes.append(f"confortável para os {temp:.0f} °C previstos")

    if ctx.vai_chover:
        partes.append("com calçado fechado por causa da chuva")

    if evento:
        rotulo = DRESS_CODE.get(evento, {}).get("rotulo", evento)
        partes.append(f"no nível de formalidade esperado para {rotulo.lower()}")

    if look.parcelas.get("cor", 0) >= 0.8:
        partes.append("e com cores que se harmonizam")

    return ". ".join([partes[0] + (", " + ", ".join(partes[1:]) if len(partes) > 1 else "")]) + "."


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
