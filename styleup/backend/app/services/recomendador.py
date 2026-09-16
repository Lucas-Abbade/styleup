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

# Quantas peças de cada papel entram no produto cartesiano.
#
# O número de combinações cresce com o produto dos três papéis: um acervo de 200
# peças bem distribuído gera algo próximo de 300 mil candidatos, e pontuar cada um
# estoura o orçamento de 3 s do RNF02. Pré-ordenamos cada papel pelo ajuste
# individual ao contexto e mantemos as melhores, o que limita o custo a
# 12³ = 1728 candidatos sem perda prática de qualidade: uma peça que não está
# entre as doze melhores do próprio papel não apareceria nos três primeiros looks.
LIMITE_POR_PAPEL = 12


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
    # Nome da cor como está gravado, já com a correção manual do usuário. A
    # explicação usa este valor em vez de recalcular a partir do HSV: se a pessoa
    # trocou "azul" por "azul-marinho", o texto tem de respeitar a correção.
    cor_nome: str = ""
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
def _ajuste_individual(peca: Peca, ctx: Contexto) -> float:
    """Quão bem uma peça isolada serve ao contexto.

    Serve só para pré-ordenar cada papel antes do corte. Não substitui o score,
    que avalia o conjunto: harmonia de cor, por exemplo, não existe para uma peça
    sozinha.
    """
    nota = 1 - abs(peca.formalidade - ctx.formalidade_alvo) / 5

    temp = ctx.temperatura_efetiva
    if temp is not None:
        centro = (peca.temp_min + peca.temp_max) / 2
        alcance = max((peca.temp_max - peca.temp_min) / 2, 1)
        nota += max(0.0, 1 - abs(temp - centro) / alcance)
    else:
        nota += 0.7

    nota += max(0.0, 1 - peca.usos_recentes / 5)
    return nota / 3


def _melhores_do_papel(pecas: list[Peca], ctx: Contexto, limite: int) -> list[Peca]:
    if len(pecas) <= limite:
        return pecas
    return sorted(pecas, key=lambda p: _ajuste_individual(p, ctx), reverse=True)[:limite]


def gerar_combinacoes(grupos: dict[str, list[Peca]], ctx: Contexto,
                      limite_por_papel: int = LIMITE_POR_PAPEL) -> list[Look]:
    """Produto cartesiano superior × inferior × calçado, mais a sobreposição.

    A sobreposição entra como peça obrigatória no frio e é ignorada no calor —
    é o que a definição de "look" no glossário chama de peça condicional.
    """
    temp = ctx.temperatura_efetiva
    precisa_sobreposicao = temp is not None and temp < LIMIAR_SOBREPOSICAO

    superiores = _melhores_do_papel(grupos["superior"], ctx, limite_por_papel)
    inferiores = _melhores_do_papel(grupos["inferior"], ctx, limite_por_papel)
    calcados = _melhores_do_papel(grupos["calcado"], ctx, limite_por_papel)

    sobreposicoes: Sequence[Peca | None]
    if precisa_sobreposicao and grupos["sobreposicao"]:
        # menos opções de agasalho: ele muda menos o resultado que as peças-base
        sobreposicoes = _melhores_do_papel(
            grupos["sobreposicao"], ctx, max(2, limite_por_papel // 3))
    else:
        # sem frio, ou sem casaco no acervo: recomenda sem a peça de sobreposição
        sobreposicoes = [None]

    looks: list[Look] = []
    for sup, inf, cal, sob in product(superiores, inferiores, calcados, sobreposicoes):
        pecas = {"superior": sup, "inferior": inf, "calcado": cal}
        if sob is not None:
            pecas["sobreposicao"] = sob
        looks.append(Look(pecas=pecas))
    return looks


# ------------------------------------------------------------------ 3. score
#
# O gargalo medido (cProfile, 200 peças) era recalcular por candidato o que
# depende só da peça ou só do par de peças. Com 1728 candidatos e ~40 peças
# distintas, `_nota_clima` era chamada 34 mil vezes para produzir 40 valores
# diferentes. `Avaliador` calcula cada coisa uma vez e reaproveita.


class Avaliador:
    """Pré-calcula tudo o que não varia entre candidatos.

    Escopo de vida: uma chamada de `recomendar`. Não é cache global — os valores
    dependem do contexto (temperatura, formalidade alvo), e um cache que
    sobrevivesse à requisição devolveria nota de ontem.

    Duas medições guiaram este desenho, nesta ordem:

    1. A versão original recalculava por candidato o que depende só da peça:
       `_nota_clima` era chamada 34 mil vezes para produzir 36 valores distintos.
    2. A primeira tentativa de conserto guardou os valores em dicionários, mas
       manteve um método e um gerador por critério — e ficou **mais lenta** que o
       original (14 ms contra 12 ms), porque em Python a chamada de método e o
       gerador custam mais que a aritmética que economizavam.

    Daí a forma final: índices inteiros, matriz plana de harmonia e um único laço
    sobre as peças do look, sem gerador e sem despacho de método no caminho
    quente.
    """

    __slots__ = ("ctx", "preferidas", "_indice", "_clima", "_estilo",
                 "_variedade", "_harmonia", "_n")

    def __init__(self, ctx: Contexto, preferidas: dict[str, float] | None = None):
        self.ctx = ctx
        self.preferidas = preferidas or {}
        self._indice: dict[str, int] = {}
        self._clima: list[float] = []
        self._estilo: list[float] = []
        self._variedade: list[float] = []
        self._harmonia: list[float] = []
        self._n = 0

    # --------------------------------------------------------- preparação
    def preparar(self, pecas: Iterable[Peca]) -> None:
        """Indexa as peças e calcula as tabelas por peça e por par."""
        itens = list(pecas)
        self._n = n = len(itens)
        self._indice = {p.id: i for i, p in enumerate(itens)}

        temp = self.ctx.temperatura_efetiva
        prefs = self.preferidas

        self._clima = [0.0] * n
        self._estilo = [0.0] * n
        self._variedade = [0.0] * n
        for i, p in enumerate(itens):
            if temp is None:
                self._clima[i] = 0.7        # sem clima, nota neutra em vez de zero
            else:
                centro = (p.temp_min + p.temp_max) / 2
                alcance = (p.temp_max - p.temp_min) / 2
                if alcance < 1:
                    alcance = 1.0
                nota = 1 - abs(temp - centro) / alcance
                self._clima[i] = nota if nota > 0 else 0.0
            self._estilo[i] = prefs.get(p.categoria, 0.5) if prefs else 0.5
            var = 1 - p.usos_recentes / 5
            self._variedade[i] = var if var > 0 else 0.0

        # Matriz plana n×n de harmonia. Um acervo filtrado tem algumas dezenas de
        # peças, então isto é kilobytes — e substitui centenas de milhares de
        # avaliações de cor por um acesso indexado.
        self._harmonia = h = [0.0] * (n * n)
        for i in range(n):
            a = itens[i]
            base = i * n
            for j in range(i + 1, n):
                b = itens[j]
                valor = harmonia(a.cor_hsv, a.neutra, b.cor_hsv, b.neutra,
                                 nome_a=a.cor_nome or None,
                                 nome_b=b.cor_nome or None)
                h[base + j] = valor
                h[j * n + i] = valor

    # ------------------------------------------------------- por candidato
    def pontuar(self, look: Look, pesos: dict[str, float]) -> Look:
        indice = self._indice
        clima = self._clima
        estilo = self._estilo
        variedade = self._variedade
        harm = self._harmonia
        n = self._n

        idxs = []
        soma_clima = soma_estilo = soma_var = 0.0
        soma_form = 0
        menor = 99
        maior = -1

        for p in look.pecas.values():
            i = indice[p.id]
            idxs.append(i)
            soma_clima += clima[i]
            soma_estilo += estilo[i]
            soma_var += variedade[i]
            f = p.formalidade
            soma_form += f
            if f < menor:
                menor = f
            if f > maior:
                maior = f

        qtd = len(idxs)

        # ocasião: distância da formalidade média ao alvo, punindo a dispersão.
        # Um blazer com chinelo tem média aceitável e dispersão alta — e é a
        # dispersão que soa errado.
        erro = abs(soma_form / qtd - self.ctx.formalidade_alvo)
        nota_erro = 1 - erro / 2
        nota_disp = 1 - (maior - menor) / 4
        ocasiao = (nota_erro if nota_erro > 0 else 0.0) * (nota_disp if nota_disp > 0 else 0.0)

        # cor: média da harmonia entre todos os pares do look
        soma_cor = 0.0
        pares = 0
        for a in range(qtd):
            linha = idxs[a] * n
            for b in range(a + 1, qtd):
                soma_cor += harm[linha + idxs[b]]
                pares += 1

        parcelas = {
            "ocasiao": ocasiao,
            "clima": soma_clima / qtd,
            "cor": (soma_cor / pares) if pares else 0.5,
            "estilo": soma_estilo / qtd,
            "variedade": soma_var / qtd,
        }

        total = 0.0
        normalizador = 0.0
        for chave, valor in parcelas.items():
            peso = pesos.get(chave, 0.0)
            total += peso * valor
            normalizador += peso
        look.score = total / normalizador if normalizador else 0.0
        look.parcelas = parcelas
        return look


def pontuar(look: Look, ctx: Contexto, pesos: dict[str, float],
            preferidas: dict[str, float] | None = None) -> Look:
    """Pontua um look isolado. Conveniência para testes e depuração.

    Em lote, use `Avaliador`: por aqui as tabelas são reconstruídas a cada
    chamada, o que anula todo o pré-cálculo.
    """
    avaliador = Avaliador(ctx, preferidas)
    avaliador.preparar(look.pecas.values())
    return avaliador.pontuar(look, pesos)


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

    candidatos_crus = gerar_combinacoes(grupos, ctx)
    avaliador = Avaliador(ctx, preferidas)
    # indexa só as peças que sobreviveram aos filtros e ao corte
    avaliador.preparar({p.id: p for l in candidatos_crus
                        for p in l.pecas.values()}.values())
    candidatos = [avaliador.pontuar(l, pesos) for l in candidatos_crus]
    candidatos.sort(key=lambda l: l.score, reverse=True)

    escolhidos: list[Look] = []
    assinaturas: set[tuple[str, ...]] = set()
    usados: set[str] = set()

    for look in candidatos:
        if len(escolhidos) >= quantidade:
            break
        # diversidade: no máximo uma peça repetida em relação ao que já entrou
        if escolhidos and len(usados.intersection(look.ids)) > 1:
            continue
        escolhidos.append(look)
        assinaturas.add(tuple(sorted(look.ids)))
        usados.update(look.ids)

    # se a diversificação for restritiva demais, completa com os melhores restantes
    for look in candidatos:
        if len(escolhidos) >= quantidade:
            break
        assinatura = tuple(sorted(look.ids))
        if assinatura not in assinaturas:
            escolhidos.append(look)
            assinaturas.add(assinatura)

    # Reordena antes de devolver. O filtro de diversidade pula candidatos e o
    # laço de reposição volta ao topo da lista, então a ordem de inserção não é
    # a ordem de score — e a posição do look é justamente o que a interface
    # apresenta como "Opção 1". Sem isto, a primeira opção pode não ser a melhor.
    escolhidos.sort(key=lambda l: l.score, reverse=True)
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
