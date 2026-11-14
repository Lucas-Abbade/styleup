"""Interpretação do pedido em texto livre da tela "Gerador de Looks".

"Look para a faculdade, all black, dia frio" vira evento, estilo e clima. É um
léxico determinístico, não um modelo de linguagem: o RNF14 proíbe dependência
paga obrigatória, e uma regra que se lê em uma tela é mais fácil de defender
diante da banca do que um prompt. O que não for reconhecido é ignorado, e a
resposta sempre diz o que foi entendido — o usuário confere em vez de adivinhar.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .taxonomia import DRESS_CODE, ESTILOS

# Ordem importa: expressões mais específicas primeiro ("home office" antes de
# "office"). Os termos já estão sem acento e em minúsculas.
_EVENTOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("casa", ("home office", "ficar em casa", "em casa", "de casa", "casa")),
    ("academia", ("academia", "treino", "treinar", "malhar", "corrida", "correr",
                  "futebol", "esporte", "gym", "caminhada")),
    ("praia", ("praia", "piscina", "clube", "cachoeira")),
    ("formal", ("casamento", "formatura", "gala", "black tie", "evento formal",
                "cerimonia", "colacao")),
    ("reuniao", ("reuniao", "entrevista", "apresentacao", "banca", "tcc", "defesa",
                 "seminario")),
    ("jantar", ("jantar", "encontro", "date", "restaurante", "aniversario")),
    ("balada", ("balada", "role", "festa", "bar", "show", "barzinho", "noite", "happy hour")),
    ("faculdade", ("faculdade", "aula", "universidade", "escola", "curso", "campus")),
    ("trabalho", ("trabalho", "trabalhar", "escritorio", "estagio", "servico",
                  "expediente", "office")),
    ("casual", ("passeio", "shopping", "cinema", "casual", "dia a dia", "passear",
                "almoco")),
)

_ESTILOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("all-black", ("all black", "total black", "todo preto", "tudo preto",
                   "todo de preto", "so preto", "look preto")),
    ("minimalista", ("minimalista", "minimal", "clean", "basico", "discreto")),
    ("esportivo", ("esportivo", "esportiva", "sport", "atletico", "athleisure")),
    ("urbano", ("urbano", "street", "streetwear", "despojado")),
    ("classico", ("classico", "elegante", "arrumado", "alinhado", "sofisticado")),
    ("colorido", ("colorido", "vibrante", "cor viva", "alegre")),
    ("terroso", ("terroso", "terrosos", "tons terrosos", "earth")),
    ("monocromatico", ("monocromatico", "tonal", "tom sobre tom")),
    ("claro", ("tons claros", "claro", "clarinho")),
    ("escuro", ("tons escuros", "escuro", "dark")),
)

_CLIMA: tuple[tuple[float, str, tuple[str, ...]], ...] = (
    (12.0, "dia frio", ("frio", "gelado", "inverno", "friozinho", "dias frios")),
    (19.0, "clima ameno", ("fresco", "ameno", "outono", "meia estacao")),
    (32.0, "dia quente", ("calor", "quente", "verao", "ensolarado", "sol", "calorao")),
)
_CHUVA = ("chuva", "chuvoso", "chovendo", "garoa", "temporal")

_TEMPERATURA = re.compile(r"(-?\d{1,2})(?:[.,]\d)?\s*(?:°|º|graus|grau|c\b)")


@dataclass
class Interpretacao:
    evento: str | None = None
    estilo: str | None = None
    temperatura: float | None = None
    chuva: bool = False
    entendido: list[str] = field(default_factory=list)   # rótulos para a interface


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e com pontuação trocada por espaço."""
    return " " + re.sub(r"[^a-z0-9]+", " ", _sem_acento(texto)).strip() + " "


def _contem(texto: str, termo: str) -> bool:
    return f" {termo} " in texto


def interpretar(texto: str | None) -> Interpretacao:
    resultado = Interpretacao()
    if not texto or not texto.strip():
        return resultado
    limpo = normalizar(texto[:300])
    bruto = _sem_acento(texto[:300])      # mantém "°" e a vírgula decimal

    # estilo antes de evento: "all black" não deve acionar "black tie", e
    # "tons claros" não deve virar outra coisa
    for chave, termos in _ESTILOS:
        if any(_contem(limpo, t) for t in termos):
            resultado.estilo = chave
            resultado.entendido.append(ESTILOS[chave]["rotulo"])
            break

    for chave, termos in _EVENTOS:
        if any(_contem(limpo, t) for t in termos):
            resultado.evento = chave
            resultado.entendido.insert(0, DRESS_CODE[chave]["rotulo"])
            break

    explicita = _TEMPERATURA.search(bruto)
    if explicita:
        valor = float(explicita.group(1))
        if -20 <= valor <= 50:
            resultado.temperatura = valor
            resultado.entendido.append(f"{valor:.0f} °C")
    if resultado.temperatura is None:
        for valor, rotulo, termos in _CLIMA:
            if any(_contem(limpo, t) for t in termos):
                resultado.temperatura = valor
                resultado.entendido.append(f"{rotulo} (~{valor:.0f} °C)")
                break

    if any(_contem(limpo, t) for t in _CHUVA):
        resultado.chuva = True
        resultado.entendido.append("chuva")

    # um pedido esportivo sem evento é, na prática, um look de treino
    if resultado.estilo == "esportivo" and resultado.evento is None:
        resultado.evento = "academia"
    return resultado
