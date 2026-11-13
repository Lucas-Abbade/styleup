"""Motor de recomendação (módulo M5 do Documento de Visão).

O fluxo é o da Figura 3: filtros rígidos → geração de combinações → score
ponderado → ranqueamento dos três melhores.

Nada aqui toca banco, rede ou arquivo. É uma função pura sobre listas de peças,
o que permite testar cada regra isoladamente e reproduzir qualquer recomendação
que um usuário questionar — exigência prática do RNF04, já que a avaliação com
usuários reais precisa ser auditável.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Iterable, Sequence

from .cor import harmonia

# Peso padrão de cada critério. É o ponto de partida de todo usuário novo; o
# módulo M6 ajusta essa mesma estrutura a partir do feedback.
PESOS_PADRAO: dict[str, float] = {
    "ocasiao": 0.30,
    "clima": 0.25,
    "cor": 0.20,
    "estilo": 0.15,
    "variedade": 0.10,
}

# Abaixo desta temperatura o motor passa a exigir uma peça de sobreposição.
LIMIAR_SOBREPOSICAO = 18.0
# Folga aceita entre a formalidade da peça e a exigida pelo evento.
FOLGA_FORMALIDADE = 1


@dataclass(frozen=True)
class Peca:
    id: str
    papel: str                 # superior | inferior | calcado | sobreposicao
    categoria: str
    formalidade: int
    cor_hsv: tuple[float, float, float]
    neutra: bool
    temp_min: float
    temp_max: float
    resiste_chuva: bool = True
    disponivel: bool = True
    usos_recentes: int = 0     # quantas vezes apareceu nos últimos looks


@dataclass(frozen=True)
class Contexto:
    formalidade_alvo: int
    temperatura: float | None = None
    sensacao: float | None = None
    chuva_prob: float | None = None

    @property
    def temperatura_efetiva(self) -> float | None:
        """A sensação térmica descreve melhor o conforto do que o termômetro."""
        return self.sensacao if self.sensacao is not None else self.temperatura

    @property
    def vai_chover(self) -> bool:
        return (self.chuva_prob or 0) >= 0.5


@dataclass
class Look:
    pecas: dict[str, Peca]                   # papel -> peça
    score: float = 0.0
    parcelas: dict[str, float] = field(default_factory=dict)

    @property
    def ids(self) -> list[str]:
        return [p.id for p in self.pecas.values()]


# --------------------------------------------------------------- 1. filtros
def passa_filtros(peca: Peca, ctx: Contexto) -> bool:
    """Filtros rígidos: eliminam o que é inviável, não o que é feio.

    Um filtro rígido nunca deve descartar por gosto — só por impedimento
    objetivo. Preferência é assunto do score.
    """
    if not peca.disponivel:
        return False

    temp = ctx.temperatura_efetiva
    if temp is not None:
        # 3 °C de tolerância: a faixa da taxonomia é uma média, não uma fronteira
        if not (peca.temp_min - 3) <= temp <= (peca.temp_max + 3):
            return False

    if ctx.vai_chover and not peca.resiste_chuva:
        return False

    if abs(peca.formalidade - ctx.formalidade_alvo) > FOLGA_FORMALIDADE:
        return False

    return True


def filtrar(pecas: Iterable[Peca], ctx: Contexto) -> dict[str, list[Peca]]:
    """Agrupa por papel apenas as peças que sobreviveram aos filtros."""
    grupos: dict[str, list[Peca]] = {
        "superior": [], "inferior": [], "calcado": [], "sobreposicao": [],
    }
    for p in pecas:
        if p.papel in grupos and passa_filtros(p, ctx):
            grupos[p.papel].append(p)
    return grupos


# ----------------------------------------------------------- 2. combinações
def gerar_combinacoes(grupos: dict[str, list[Peca]], ctx: Contexto) -> list[Look]:
    """Produto cartesiano superior × inferior × calçado, mais a sobreposição.

    A sobreposição entra como peça obrigatória no frio e é ignorada no calor —
    é o que a definição de "look" no glossário chama de peça condicional.
    """
    temp = ctx.temperatura_efetiva
    precisa_sobreposicao = temp is not None and temp < LIMIAR_SOBREPOSICAO

    sobreposicoes: Sequence[Peca | None]
    if precisa_sobreposicao and grupos["sobreposicao"]:
        sobreposicoes = grupos["sobreposicao"]
    elif precisa_sobreposicao:
        sobreposicoes = [None]          # sem casaco no acervo: recomenda mesmo assim
    else:
        sobreposicoes = [None]

    looks: list[Look] = []
    for sup, inf, cal, sob in product(
        grupos["superior"], grupos["inferior"], grupos["calcado"], sobreposicoes
    ):
        pecas = {"superior": sup, "inferior": inf, "calcado": cal}
        if sob is not None:
            pecas["sobreposicao"] = sob
        looks.append(Look(pecas=pecas))
    return looks


# ------------------------------------------------------------------ 3. score
def _nota_ocasiao(look: Look, ctx: Contexto) -> float:
    """Quanto a formalidade média do look se aproxima da exigida pelo evento."""
    valores = [p.formalidade for p in look.pecas.values()]
    media = sum(valores) / len(valores)
    erro = abs(media - ctx.formalidade_alvo)
    # coerência interna: um blazer com chinelo tem formalidade média aceitável,
    # mas dispersão alta — e é justamente isso que soa errado.
    dispersao = max(valores) - min(valores)
    return max(0.0, 1 - erro / 2) * max(0.0, 1 - dispersao / 4)


def _nota_clima(look: Look, ctx: Contexto) -> float:
    temp = ctx.temperatura_efetiva
    if temp is None:
        return 0.7                       # sem clima, nota neutra em vez de zero
    notas = []
    for p in look.pecas.values():
        centro = (p.temp_min + p.temp_max) / 2
        alcance = max((p.temp_max - p.temp_min) / 2, 1)
        notas.append(max(0.0, 1 - abs(temp - centro) / alcance))
    return sum(notas) / len(notas)


def _nota_cor(look: Look) -> float:
    """Média da harmonia entre todos os pares de peças do look."""
    itens = list(look.pecas.values())
    pares = [
        harmonia(a.cor_hsv, a.neutra, b.cor_hsv, b.neutra)
        for i, a in enumerate(itens)
        for b in itens[i + 1:]
    ]
    return sum(pares) / len(pares) if pares else 0.5


def _nota_estilo(look: Look, preferidas: dict[str, float]) -> float:
    """Aprendizado por feedback: categorias que o usuário aprovou pesam mais."""
    if not preferidas:
        return 0.5
    notas = [preferidas.get(p.categoria, 0.5) for p in look.pecas.values()]
    return sum(notas) / len(notas)


def _nota_variedade(look: Look) -> float:
    """Penaliza repetir as mesmas peças; é o que evita o mesmo look todo dia."""
    usos = [p.usos_recentes for p in look.pecas.values()]
    return max(0.0, 1 - (sum(usos) / len(usos)) / 5)


def pontuar(look: Look, ctx: Contexto, pesos: dict[str, float],
            preferidas: dict[str, float] | None = None) -> Look:
    parcelas = {
        "ocasiao": _nota_ocasiao(look, ctx),
        "clima": _nota_clima(look, ctx),
        "cor": _nota_cor(look),
        "estilo": _nota_estilo(look, preferidas or {}),
        "variedade": _nota_variedade(look),
    }
    total = sum(pesos.get(k, 0) * v for k, v in parcelas.items())
    normalizador = sum(pesos.get(k, 0) for k in parcelas) or 1
    look.score = total / normalizador
    look.parcelas = parcelas
    return look


# ------------------------------------------------------------ 4. orquestração
def recomendar(
    pecas: Iterable[Peca],
    ctx: Contexto,
    pesos: dict[str, float] | None = None,
    preferidas: dict[str, float] | None = None,
    quantidade: int = 3,
) -> list[Look]:
    """Ponta a ponta: filtra, combina, pontua e devolve os melhores looks.

    Os resultados são diversificados: não adianta devolver três variações da
    mesma camiseta, porque o Hit Rate@3 do RNF04 mede se *alguma* das três
    opções agradou, e três quase-iguais valem por uma.
    """
    pesos = pesos or PESOS_PADRAO
    grupos = filtrar(pecas, ctx)

    faltando = [p for p in ("superior", "inferior", "calcado") if not grupos[p]]
    if faltando:
        raise SemPecasSuficientes(faltando)

    candidatos = [pontuar(l, ctx, pesos, preferidas)
                  for l in gerar_combinacoes(grupos, ctx)]
    candidatos.sort(key=lambda l: l.score, reverse=True)

    escolhidos: list[Look] = []
    usados: set[str] = set()
    for look in candidatos:
        if len(escolhidos) >= quantidade:
            break
        # diversidade: no máximo uma peça repetida em relação ao que já entrou
        repetidas = len(usados.intersection(look.ids))
        if escolhidos and repetidas > 1:
            continue
        escolhidos.append(look)
        usados.update(look.ids)

    # se a diversificação for restritiva demais, completa com os melhores restantes
    if len(escolhidos) < quantidade:
        for look in candidatos:
            if look not in escolhidos:
                escolhidos.append(look)
            if len(escolhidos) >= quantidade:
                break

    return escolhidos[:quantidade]


class SemPecasSuficientes(Exception):
    """Nenhuma combinação é possível: falta peça em algum papel obrigatório."""

    def __init__(self, papeis: list[str]):
        self.papeis = papeis
        super().__init__(
            "Sem peças disponíveis para: " + ", ".join(papeis)
        )


# ------------------------------------------------------- 5. ajuste dos pesos
def ajustar_pesos(pesos: dict[str, float], parcelas: dict[str, float],
                  aprovado: bool, taxa: float = 0.05) -> dict[str, float]:
    """Move os pesos na direção do que explicou a aprovação (ou contra ela).

    Regra: um critério que estava alto num look aprovado ganha peso; num look
    rejeitado, perde. A soma é renormalizada para 1, então os pesos continuam
    comparáveis entre usuários.
    """
    sinal = 1 if aprovado else -1
    medio = sum(parcelas.values()) / len(parcelas)
    novos = {
        k: max(0.02, v + sinal * taxa * (parcelas.get(k, medio) - medio))
        for k, v in pesos.items()
    }
    total = sum(novos.values())
    return {k: round(v / total, 4) for k, v in novos.items()}
