"""Motor de recomendação (módulo M5 do Documento de Visão).

O fluxo é o da Figura 3: filtros rígidos → geração de combinações → score
ponderado → ranqueamento dos três melhores.

Nada aqui toca banco, rede ou arquivo. É uma função pura sobre listas de peças,
o que permite testar cada regra isoladamente e reproduzir qualquer recomendação
que um usuário questionar — exigência prática do RNF04, já que a avaliação com
usuários reais precisa ser auditável.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from typing import Iterable, Sequence

from .cor import TERROSAS, distancia_matiz, harmonia, hex_para_hsv, hex_valido
from .taxonomia import DRESS_CODE, ESTILOS, PAPEIS, POR_CHAVE

log = logging.getLogger(__name__)

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
# Entre os dois limiares a sobreposição é opcional: o score decide.
LIMIAR_SOBREPOSICAO_OPCIONAL = 22.0
# Folga aceita entre a formalidade da peça e a exigida pelo evento.
FOLGA_FORMALIDADE = 1
# Tolerância, em °C, em torno da faixa de conforto da taxonomia.
TOLERANCIA_TEMPERATURA = 3.0

# Pré-filtro (RNF02): só as N melhores peças de cada papel entram no produto
# cartesiano. Sem isto, 30 × 20 × 10 × 10 peças viram 60 mil looks em Python
# puro; com 12 × 12 × 12 × 6 o teto é ~10 mil, na casa de dezenas de ms.
TOP_N_POR_PAPEL = 12
TOP_N_SOBREPOSICAO = 6
# Quantos dos melhores looks disputam a seleção diversificada.
CANDIDATOS_DIVERSIDADE = 300
# MMR (Carbonell & Goldstein, 1998): 1 = só relevância, 0 = só diversidade.
LAMBDA_DIVERSIDADE = 0.7
MAX_ACESSORIOS = 2
# Cinto só faz sentido em calça com passante.
_INFERIOR_COM_CINTO = {"calca-jeans", "calca-sarja", "calca-social", "bermuda"}
# Abaixo disto, o look não atende à diretriz de estilo pedida e o usuário é avisado.
ESTILO_ATENDIDO = 0.6

_PESO_PAR = {
    frozenset(("superior", "inferior")): 3.0,
    frozenset(("superior", "sobreposicao")): 2.5,
    frozenset(("sobreposicao", "inferior")): 2.0,
    frozenset(("inferior", "calcado")): 1.5,
    frozenset(("superior", "calcado")): 1.0,
    frozenset(("sobreposicao", "calcado")): 1.0,
}


@dataclass(frozen=True)
class Peca:
    id: str
    papel: str                 # superior | inferior | calcado | sobreposicao | acessorio
    categoria: str
    formalidade: int
    cor_hsv: tuple[float, float, float]
    neutra: bool
    temp_min: float
    temp_max: float
    resiste_chuva: bool = True
    disponivel: bool = True
    usos_recentes: int = 0     # quantas vezes apareceu nos últimos looks
    cor_nome: str = ""         # o nome que o usuário vê (e pode ter corrigido)
    estampa: str | None = None


@dataclass(frozen=True)
class Contexto:
    formalidade_alvo: int
    temperatura: float | None = None
    sensacao: float | None = None
    chuva_prob: float | None = None
    evento: str | None = None      # chave de DRESS_CODE; habilita vetos e preferências
    estilo: str | None = None      # chave de ESTILOS; diretriz pedida pelo usuário

    @property
    def temperatura_efetiva(self) -> float | None:
        """A sensação térmica descreve melhor o conforto do que o termômetro."""
        return self.sensacao if self.sensacao is not None else self.temperatura

    @property
    def vai_chover(self) -> bool:
        return (self.chuva_prob or 0) >= 0.5

    @property
    def pede_sobreposicao(self) -> bool:
        temp = self.temperatura_efetiva
        return temp is not None and temp < LIMIAR_SOBREPOSICAO


@dataclass
class Look:
    pecas: dict[str, Peca]                   # papel -> peça
    score: float = 0.0
    parcelas: dict[str, float] = field(default_factory=dict)
    acessorios: list[Peca] = field(default_factory=list)

    @property
    def ids(self) -> list[str]:
        return [p.id for p in self.pecas.values()] + [a.id for a in self.acessorios]

    @property
    def todas(self) -> list[tuple[str, Peca]]:
        """(papel, peça) na ordem de exibição, acessórios por último."""
        return list(self.pecas.items()) + [("acessorio", a) for a in self.acessorios]


@dataclass
class Resultado:
    looks: list[Look]
    avisos: list[str] = field(default_factory=list)   # o que foi flexibilizado, se algo


class SemPecasSuficientes(Exception):
    """Nenhuma combinação é possível: falta peça em algum papel obrigatório."""

    def __init__(self, papeis: list[str]):
        self.papeis = papeis
        super().__init__(
            "Sem peças disponíveis para: " + ", ".join(papeis)
        )


# ----------------------------------------------------- 0. entrada defensiva
def peca_de_linha(linha: dict, usos: int = 0) -> Peca | None:
    """Converte uma linha do banco em `Peca`; devolve None se estiver malformada.

    Uma peça com `cor_hsv` de tamanho errado ou formalidade nula não pode
    derrubar a recomendação inteira do usuário: ela é ignorada (e registrada),
    e o resto do guarda-roupa segue valendo.
    """
    try:
        hsv = linha.get("cor_hsv")
        if not isinstance(hsv, (list, tuple)) or len(hsv) != 3:
            if not hex_valido(linha.get("cor_hex", "")):
                raise ValueError("cor_hsv e cor_hex inválidos")
            hsv = hex_para_hsv(linha["cor_hex"])
        h, s, v = (float(x) for x in hsv)
        if not (math.isfinite(h) and 0 <= s <= 1 and 0 <= v <= 1):
            raise ValueError("cor_hsv fora da faixa")
        papel = linha["papel"]
        if papel not in PAPEIS:
            raise ValueError(f"papel desconhecido: {papel}")
        formalidade = int(linha["formalidade"])
        if not 1 <= formalidade <= 5:
            raise ValueError("formalidade fora de 1-5")
        return Peca(
            id=str(linha["id"]), papel=papel, categoria=str(linha["categoria"]),
            formalidade=formalidade, cor_hsv=(h % 360, s, v),
            neutra=bool(linha.get("neutra", False)),
            temp_min=float(linha.get("temp_min", 0)),
            temp_max=float(linha.get("temp_max", 45)),
            resiste_chuva=bool(linha.get("resiste_chuva", True)),
            disponivel=bool(linha.get("disponivel", True)),
            usos_recentes=usos,
            cor_nome=str(linha.get("cor_nome") or ""),
            estampa=(linha.get("atributos") or {}).get("estampa"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        log.warning("Peça %s ignorada na recomendação: %s", linha.get("id"), exc)
        return None


# --------------------------------------------------------------- 1. filtros
def passa_filtros(peca: Peca, ctx: Contexto, *,
                  tolerancia: float | None = TOLERANCIA_TEMPERATURA,
                  folga: int | None = None, vetos: bool = True,
                  chuva: bool = True) -> bool:
    """Filtros rígidos: eliminam o que é inviável, não o que é feio.

    Um filtro rígido nunca deve descartar por gosto — só por impedimento
    objetivo. Preferência é assunto do score. Os parâmetros nomeados existem
    para a degradação controlada (ver `recomendar`): `tolerancia=None` ignora a
    temperatura, `vetos=False` ignora os vetos do evento.
    """
    if not peca.disponivel:
        return False

    temp = ctx.temperatura_efetiva
    if temp is not None and tolerancia is not None:
        # a faixa da taxonomia é uma média, não uma fronteira
        if not (peca.temp_min - tolerancia) <= temp <= (peca.temp_max + tolerancia):
            return False

    if chuva and ctx.vai_chover and not peca.resiste_chuva:
        return False

    cat = POR_CHAVE.get(peca.categoria)
    if folga is None:
        folga = cat.folga_formalidade if cat else FOLGA_FORMALIDADE
    if abs(peca.formalidade - ctx.formalidade_alvo) > folga:
        return False

    if vetos and ctx.evento and peca.categoria in DRESS_CODE.get(ctx.evento, {}).get("vetadas", ()):
        return False

    return True


def filtrar(pecas: Iterable[Peca], ctx: Contexto, **relaxamento) -> dict[str, list[Peca]]:
    """Agrupa por papel apenas as peças que sobreviveram aos filtros."""
    grupos: dict[str, list[Peca]] = {p: [] for p in PAPEIS}
    for p in pecas:
        if p.papel in grupos and passa_filtros(p, ctx, **relaxamento):
            grupos[p.papel].append(p)
    return grupos


# Degradação controlada (RNF07). Cada papel usa o primeiro nível em que tem ao
# menos uma peça; quem já tem candidatos no nível estrito não é afetado.
_NIVEIS: tuple[tuple[dict, str], ...] = (
    ({}, ""),
    ({"tolerancia": 7.0},
     "ampliei a faixa de temperatura aceita"),
    ({"tolerancia": None},
     "ignorei a faixa de temperatura, porque nada no guarda-roupa serve a este clima"),
    ({"tolerancia": None, "folga": 2, "vetos": False, "chuva": False},
     "aceitei peças fora do nível de formalidade do evento"),
)
_NOME_PAPEL = {"superior": "parte de cima", "inferior": "parte de baixo",
               "calcado": "calçado", "sobreposicao": "sobreposição",
               "acessorio": "acessório"}


def _filtrar_com_degradacao(pecas: Sequence[Peca], ctx: Contexto
                            ) -> tuple[dict[str, list[Peca]], list[str]]:
    grupos = filtrar(pecas, ctx)
    avisos: list[str] = []
    for papel in ("superior", "inferior", "calcado"):
        if grupos[papel]:
            continue
        do_papel = [p for p in pecas if p.papel == papel]
        for relaxamento, descricao in _NIVEIS[1:]:
            achadas = [p for p in do_papel if passa_filtros(p, ctx, **relaxamento)]
            if achadas:
                grupos[papel] = achadas
                avisos.append(f"Para {_NOME_PAPEL[papel]}, {descricao}.")
                break
    return grupos, avisos


# ----------------------------------------------------------- 2. combinações
def gerar_combinacoes(grupos: dict[str, list[Peca]], ctx: Contexto) -> list[Look]:
    """Produto cartesiano superior × inferior × calçado, mais a sobreposição.

    A sobreposição é obrigatória no frio (quando existe no acervo), opcional na
    meia-estação e em eventos sociais — onde o blazer completa o traje — e
    ignorada no calor. É a "peça condicional" da definição de look no glossário.
    """
    temp = ctx.temperatura_efetiva
    disponiveis = grupos.get("sobreposicao", [])

    sobreposicoes: Sequence[Peca | None]
    if ctx.pede_sobreposicao and disponiveis:
        sobreposicoes = disponiveis
    elif ctx.pede_sobreposicao:
        sobreposicoes = [None]          # sem casaco no acervo: recomenda mesmo assim
    elif disponiveis and ((temp is not None and temp < LIMIAR_SOBREPOSICAO_OPCIONAL)
                          or ctx.formalidade_alvo >= 4):
        sobreposicoes = [None, *disponiveis]
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
@lru_cache(maxsize=8192)
def _conforto(peca: Peca, temp: float) -> float:
    """Conforto térmico de uma peça na temperatura dada (0 a 1).

    Duas leituras da mesma faixa da taxonomia, combinadas:

    * **platô** — dentro da faixa a peça é aceitável: 1,0 no miolo, 0,75 na
      borda, e cai 0,15 por grau fora dela;
    * **centro** — quanto mais perto do meio da faixa, mais a peça é a escolha
      natural para aquele dia.

    Só o centro (versão anterior) dava 0,15 a uma camiseta num dia de 20 °C,
    dentro da faixa dela. Só o platô empata calça jeans e bermuda aos 32 °C. A
    mistura mantém as duas coisas: nada dentro da faixa é punido demais, e a
    bermuda ganha da calça no calor.
    """
    if peca.temp_min <= temp <= peca.temp_max:
        margem = min(temp - peca.temp_min, peca.temp_max - temp)
        plato = 0.75 + 0.25 * min(1.0, margem / 5)
    else:
        fora = (peca.temp_min - temp) if temp < peca.temp_min else (temp - peca.temp_max)
        plato = max(0.0, 0.75 - 0.15 * fora)
    centro = (peca.temp_min + peca.temp_max) / 2
    alcance = max((peca.temp_max - peca.temp_min) / 2, 1)
    return 0.6 * plato + 0.4 * max(0.0, 1 - abs(temp - centro) / alcance)


def _nota_ocasiao(look: Look, ctx: Contexto) -> float:
    """Quanto a formalidade média do look se aproxima da exigida pelo evento."""
    valores = [p.formalidade for p in look.pecas.values()]
    media = sum(valores) / len(valores)
    erro = abs(media - ctx.formalidade_alvo)
    # coerência interna: um blazer com chinelo tem formalidade média aceitável,
    # mas dispersão alta — e é justamente isso que soa errado.
    dispersao = max(valores) - min(valores)
    nota = max(0.0, 1 - erro / 2) * max(0.0, 1 - dispersao / 4)

    preferidas = DRESS_CODE.get(ctx.evento or "", {}).get("preferidas", ())
    if preferidas:
        fracao = sum(p.categoria in preferidas for p in look.pecas.values()) / len(valores)
        nota *= 0.80 + 0.20 * fracao
    # em evento social o traje fica incompleto sem a peça de cima do conjunto
    if (ctx.formalidade_alvo >= 4 and "sobreposicao" not in look.pecas
            and (ctx.temperatura_efetiva is None or ctx.temperatura_efetiva <= 28)):
        nota *= 0.82 if ctx.formalidade_alvo >= 5 else 0.93
    return nota


def _nota_clima(look: Look, ctx: Contexto) -> float:
    temp = ctx.temperatura_efetiva
    if temp is None:
        return 0.7                       # sem clima, nota neutra em vez de zero
    notas = [_conforto(p, temp) for p in look.pecas.values()]
    return sum(notas) / len(notas)


@lru_cache(maxsize=4096)
def cor_efetiva(peca: Peca) -> tuple[tuple[float, float, float], bool]:
    """Cor da peça como o olho a trata numa combinação.

    Jeans azul é neutro na prática — vai com qualquer camiseta —, embora o seu
    matiz não seja. A marca vem do material (taxonomia), não de um limiar de
    saturação: um denim médio é bem saturado.
    """
    cat = POR_CHAVE.get(peca.categoria)
    if cat and cat.denim and 185 <= peca.cor_hsv[0] <= 255:
        return peca.cor_hsv, True
    return peca.cor_hsv, peca.neutra


def _familias_de_matiz(cores: list[tuple[float, float, float]]) -> int:
    """Quantos matizes distintos (separados por mais de 30°) há na lista."""
    familias: list[float] = []
    for h, _, _ in cores:
        if all(distancia_matiz(h, f) > 30 for f in familias):
            familias.append(h)
    return len(familias)


def _nota_cor(look: Look) -> float:
    """Harmonia do conjunto: pares ponderados pela área visível, menos excessos.

    Camisa e calça ocupam quase todo o campo visual, então o par pesa três vezes
    mais que camisa e calçado. Depois vêm duas regras de conjunto que a média de
    pares não enxerga: cores demais (mais de dois matizes) e estampas demais.
    """
    itens = [(papel, *cor_efetiva(p)) for papel, p in look.pecas.items()]
    total = peso_total = 0.0
    for i, (papel_a, cor_a, neutra_a) in enumerate(itens):
        for papel_b, cor_b, neutra_b in itens[i + 1:]:
            peso = _PESO_PAR.get(frozenset((papel_a, papel_b)), 1.0)
            total += peso * harmonia(cor_a, neutra_a, cor_b, neutra_b)
            peso_total += peso
    nota = total / peso_total if peso_total else 0.5

    coloridas = [cor for _, cor, neutra in itens if not neutra]
    nota -= 0.10 * max(0, _familias_de_matiz(coloridas) - 2)

    estampadas = sum(1 for p in look.pecas.values() if p.estampa not in (None, "", "lisa"))
    if estampadas == 2:
        nota *= 0.93
    elif estampadas >= 3:
        nota *= 0.80
    return max(0.0, min(1.0, nota))


def _fracao(look: Look, criterio) -> float:
    pecas = list(look.pecas.values())
    return sum(1 for p in pecas if criterio(p)) / len(pecas)


def nota_estilo_pedido(look: Look, estilo: str) -> float:
    """Quanto o look atende à diretriz que o usuário pediu (0 a 1)."""
    pecas = list(look.pecas.values())
    efetivas = [cor_efetiva(p) for p in pecas]
    cat = POR_CHAVE.get

    if estilo == "all-black":
        return sum(1.0 if p.cor_nome == "preto" or p.cor_hsv[2] < 0.14
                   else 0.5 if p.cor_nome == "grafite" or p.cor_hsv[2] < 0.25
                   else 0.0 for p in pecas) / len(pecas)
    if estilo == "minimalista":
        neutras = sum(1 for _, neutra in efetivas if neutra) / len(pecas)
        lisas = _fracao(look, lambda p: p.estampa in (None, "", "lisa"))
        return 0.7 * neutras + 0.3 * lisas
    if estilo == "colorido":
        return min(1.0, sum(1 for _, neutra in efetivas if not neutra) / 2)
    if estilo == "terroso":
        return _fracao(look, lambda p: p.cor_nome in TERROSAS)
    if estilo == "monocromatico":
        coloridas = [cor for cor, neutra in efetivas if not neutra]
        if not coloridas:
            claridades = [cor[2] for cor, _ in efetivas]
            return 1.0 if max(claridades) - min(claridades) < 0.35 else 0.6
        return 1.0 if _familias_de_matiz(coloridas) == 1 else 0.2
    if estilo == "claro":
        return _fracao(look, lambda p: p.cor_hsv[2] >= 0.70 and p.cor_hsv[1] <= 0.45)
    if estilo == "escuro":
        return _fracao(look, lambda p: p.cor_hsv[2] <= 0.40)
    if estilo == "esportivo":
        return _fracao(look, lambda p: bool(cat(p.categoria) and cat(p.categoria).esportiva))
    if estilo == "urbano":
        return _fracao(look, lambda p: bool(cat(p.categoria) and cat(p.categoria).urbana))
    if estilo == "classico":
        alinhadas = _fracao(look, lambda p: p.formalidade >= 3)
        neutras = sum(1 for _, neutra in efetivas if neutra) / len(pecas)
        return 0.6 * alinhadas + 0.4 * neutras
    return 0.5


def _nota_estilo(look: Look, preferidas: dict[str, float],
                 estilo: str | None = None) -> float:
    """Aprendizado por feedback: categorias que o usuário aprovou pesam mais.

    Quando há uma diretriz explícita ("minimalista"), ela divide o critério com
    o histórico: o pedido de agora vale tanto quanto o gosto aprendido.
    """
    aprendido = 0.5
    if preferidas:
        notas = [preferidas.get(p.categoria, 0.5) for p in look.pecas.values()]
        aprendido = sum(notas) / len(notas)
    if not estilo:
        return aprendido
    return 0.35 * aprendido + 0.65 * nota_estilo_pedido(look, estilo)


def _nota_variedade(look: Look) -> float:
    """Penaliza repetir as mesmas peças; é o que evita o mesmo look todo dia."""
    usos = [p.usos_recentes for p in look.pecas.values()]
    return max(0.0, 1 - (sum(usos) / len(usos)) / 5)


def _pesos_efetivos(pesos: dict[str, float], ctx: Contexto) -> dict[str, float]:
    """Um pedido explícito de estilo dobra o peso do critério naquela consulta."""
    if not ctx.estilo:
        return pesos
    return {**pesos, "estilo": pesos.get("estilo", 0) * 2 + 0.10}


def pontuar(look: Look, ctx: Contexto, pesos: dict[str, float],
            preferidas: dict[str, float] | None = None) -> Look:
    parcelas = {
        "ocasiao": _nota_ocasiao(look, ctx),
        "clima": _nota_clima(look, ctx),
        "cor": _nota_cor(look),
        "estilo": _nota_estilo(look, preferidas or {}, ctx.estilo),
        "variedade": _nota_variedade(look),
    }
    efetivos = _pesos_efetivos(pesos, ctx)
    total = sum(efetivos.get(k, 0) * v for k, v in parcelas.items())
    normalizador = sum(efetivos.get(k, 0) for k in parcelas) or 1
    look.score = total / normalizador
    look.parcelas = parcelas
    return look


# -------------------------------------------------------- 3b. pré-filtro
def _nota_individual(peca: Peca, ctx: Contexto, pesos: dict[str, float],
                     preferidas: dict[str, float]) -> float:
    """Parte do score que depende só da peça (tudo menos a harmonia de cor)."""
    temp = ctx.temperatura_efetiva
    return (
        pesos.get("ocasiao", 0) * max(0.0, 1 - abs(peca.formalidade - ctx.formalidade_alvo) / 2)
        + pesos.get("clima", 0) * (_conforto(peca, temp) if temp is not None else 0.7)
        + pesos.get("estilo", 0) * preferidas.get(peca.categoria, 0.5)
        + pesos.get("variedade", 0) * max(0.0, 1 - peca.usos_recentes / 5)
    )


def _melhores(grupo: list[Peca], limite: int, ctx: Contexto, pesos: dict[str, float],
              preferidas: dict[str, float]) -> list[Peca]:
    """As `limite` melhores peças do papel, preservando variedade de cor.

    O corte usa a nota individual, que não enxerga harmonia; por isso as três
    últimas vagas são reservadas a cores ainda não representadas — uma peça
    mediana de cor diferente pode ser justamente a que fecha a melhor combinação.
    """
    if len(grupo) <= limite:
        return grupo
    ordenadas = sorted(grupo, key=lambda p: _nota_individual(p, ctx, pesos, preferidas),
                       reverse=True)
    reserva = min(3, limite // 3)
    escolhidas = ordenadas[:limite - reserva]
    cores = {p.cor_nome or round(p.cor_hsv[0] / 30) for p in escolhidas}
    resto = ordenadas[limite - reserva:]
    for p in resto:
        if len(escolhidas) >= limite:
            break
        chave = p.cor_nome or round(p.cor_hsv[0] / 30)
        if chave not in cores:
            escolhidas.append(p)
            cores.add(chave)
    for p in resto:
        if len(escolhidas) >= limite:
            break
        if p not in escolhidas:
            escolhidas.append(p)
    return escolhidas


# ------------------------------------------------------ 3c. diversificação
def _semelhanca(a: Look, b: Look) -> float:
    """Jaccard sobre as peças principais (acessórios não contam)."""
    ids_a = {p.id for p in a.pecas.values()}
    ids_b = {p.id for p in b.pecas.values()}
    return len(ids_a & ids_b) / len(ids_a | ids_b)


def _mesma_base(a: Look, b: Look) -> bool:
    return (a.pecas["superior"].id == b.pecas["superior"].id
            and a.pecas["inferior"].id == b.pecas["inferior"].id)


def _diversificar(candidatos: list[Look], quantidade: int) -> list[Look]:
    """Seleção gulosa por MMR: relevância menos semelhança com o que já entrou.

    O Hit Rate@3 mede se *alguma* das três opções agradou; três variações da
    mesma camisa e calça valem por uma. Por isso, além do MMR, dois looks não
    repetem a mesma dupla de cima e de baixo enquanto houver alternativa.
    """
    if not candidatos:
        return []
    escolhidos = [candidatos[0]]
    restantes = candidatos[1:CANDIDATOS_DIVERSIDADE]
    while len(escolhidos) < quantidade and restantes:
        livres = [c for c in restantes
                  if not any(_mesma_base(c, e) for e in escolhidos)] or restantes
        melhor = max(livres, key=lambda c: (
            LAMBDA_DIVERSIDADE * c.score
            - (1 - LAMBDA_DIVERSIDADE) * max(_semelhanca(c, e) for e in escolhidos)))
        escolhidos.append(melhor)
        restantes.remove(melhor)
    return escolhidos


# ------------------------------------------------------------ 3d. acessórios
def _acrescentar_acessorios(looks: list[Look], disponiveis: list[Peca]) -> None:
    """Até dois acessórios por look, um por região do corpo, que combinem em cor.

    Entram depois da escolha dos looks e não mexem no score: acessório é
    acabamento, não critério — e assim o motor continua explicável pelas cinco
    parcelas. Um mesmo acessório só se repete entre looks se não houver outro.
    """
    usados: set[str] = set()
    for look in looks:
        base = [cor_efetiva(p) for p in look.pecas.values()]
        avaliados = []
        for a in disponiveis:
            if (a.categoria == "cinto"
                    and look.pecas["inferior"].categoria not in _INFERIOR_COM_CINTO):
                continue
            cor, neutra = cor_efetiva(a)
            nota = sum(harmonia(cor, neutra, c, n) for c, n in base) / len(base)
            if nota >= 0.75:
                avaliados.append((nota - (0.2 if a.id in usados else 0)
                                  - 0.03 * a.usos_recentes, a))
        avaliados.sort(key=lambda par: par[0], reverse=True)
        regioes: set[str] = set()
        for _, a in avaliados:
            cat = POR_CHAVE.get(a.categoria)
            regiao = (cat.regiao if cat and cat.regiao else a.categoria)
            if regiao in regioes:
                continue
            look.acessorios.append(a)
            regioes.add(regiao)
            usados.add(a.id)
            if len(look.acessorios) >= MAX_ACESSORIOS:
                break


# ------------------------------------------------------------ 4. orquestração
def recomendar_com_avisos(
    pecas: Iterable[Peca],
    ctx: Contexto,
    pesos: dict[str, float] | None = None,
    preferidas: dict[str, float] | None = None,
    quantidade: int = 3,
) -> Resultado:
    """Ponta a ponta: filtra, combina, pontua e devolve os melhores looks.

    Os resultados são diversificados: não adianta devolver três variações da
    mesma camiseta, porque o Hit Rate@3 do RNF04 mede se *alguma* das três
    opções agradou, e três quase-iguais valem por uma.

    Quando um papel obrigatório não tem peça que passe nos filtros estritos, o
    motor afrouxa os filtros só daquele papel e diz o que fez em `avisos` — é a
    degradação do RNF07. `SemPecasSuficientes` fica reservado ao caso em que o
    papel realmente não existe no guarda-roupa.
    """
    pesos = normalizar_pesos(pesos)
    preferidas = preferidas or {}
    pecas = list(pecas)
    grupos, avisos = _filtrar_com_degradacao(pecas, ctx)

    faltando = [p for p in ("superior", "inferior", "calcado") if not grupos[p]]
    if faltando:
        raise SemPecasSuficientes(faltando)

    for papel in ("superior", "inferior", "calcado"):
        grupos[papel] = _melhores(grupos[papel], TOP_N_POR_PAPEL, ctx, pesos, preferidas)
    grupos["sobreposicao"] = _melhores(grupos["sobreposicao"], TOP_N_SOBREPOSICAO,
                                       ctx, pesos, preferidas)

    candidatos = [pontuar(l, ctx, pesos, preferidas)
                  for l in gerar_combinacoes(grupos, ctx)]
    candidatos.sort(key=lambda l: l.score, reverse=True)

    escolhidos = _diversificar(candidatos, quantidade)
    _acrescentar_acessorios(escolhidos, grupos["acessorio"])

    if (ctx.estilo and escolhidos
            and nota_estilo_pedido(escolhidos[0], ctx.estilo) < ESTILO_ATENDIDO):
        rotulo = ESTILOS[ctx.estilo]["rotulo"].lower() if ctx.estilo in ESTILOS else ctx.estilo
        avisos.append(f"Seu guarda-roupa não tem peças suficientes para um look {rotulo} "
                      "neste contexto; estas são as combinações mais próximas.")
    if ctx.pede_sobreposicao and not grupos["sobreposicao"]:
        avisos.append("Está frio e não há sobreposição disponível no guarda-roupa; "
                      "os looks vão sem agasalho.")
    return Resultado(looks=escolhidos, avisos=avisos)


def recomendar(
    pecas: Iterable[Peca],
    ctx: Contexto,
    pesos: dict[str, float] | None = None,
    preferidas: dict[str, float] | None = None,
    quantidade: int = 3,
) -> list[Look]:
    """Atalho que devolve só os looks (ver `recomendar_com_avisos`)."""
    return recomendar_com_avisos(pecas, ctx, pesos, preferidas, quantidade).looks


# ------------------------------------------------------- 5. ajuste dos pesos
def pesos_validos(pesos: object) -> bool:
    """Exatamente os cinco critérios, todos positivos, somando 1."""
    if not isinstance(pesos, dict) or set(pesos) != set(PESOS_PADRAO):
        return False
    try:
        valores = [float(v) for v in pesos.values()]
    except (TypeError, ValueError):
        return False
    return (all(math.isfinite(v) and v > 0 for v in valores)
            and abs(sum(valores) - 1.0) <= 0.01)


def normalizar_pesos(pesos: dict[str, float] | None) -> dict[str, float]:
    """Pesos utilizáveis a partir do que vier do banco.

    Um JSON corrompido em `preferencias.pesos` (chave faltando, valor negativo,
    texto) não pode quebrar a recomendação: nesse caso voltamos ao padrão.
    """
    if not pesos:
        return dict(PESOS_PADRAO)
    try:
        limpos = {k: float(pesos[k]) for k in PESOS_PADRAO}
    except (KeyError, TypeError, ValueError):
        return dict(PESOS_PADRAO)
    if any(not math.isfinite(v) or v <= 0 for v in limpos.values()):
        return dict(PESOS_PADRAO)
    total = sum(limpos.values())
    return {k: v / total for k, v in limpos.items()}


def ajustar_pesos(pesos: dict[str, float], parcelas: dict[str, float],
                  aprovado: bool, taxa: float = 0.05) -> dict[str, float]:
    """Move os pesos na direção do que explicou a aprovação (ou contra ela).

    Regra: um critério que estava alto num look aprovado ganha peso; num look
    rejeitado, perde. A soma é renormalizada para 1, então os pesos continuam
    comparáveis entre usuários.

    Um look sem parcelas (registro antigo ou gravado pela metade) não ensina
    nada: os pesos voltam como estavam, em vez de dividir por zero.
    """
    pesos = normalizar_pesos(pesos)
    validas = {k: float(v) for k, v in (parcelas or {}).items()
               if k in pesos and isinstance(v, (int, float)) and math.isfinite(v)}
    if not validas:
        return {k: round(v, 4) for k, v in pesos.items()}

    sinal = 1 if aprovado else -1
    medio = sum(validas.values()) / len(validas)
    novos = {
        k: max(0.02, v + sinal * taxa * (validas.get(k, medio) - medio))
        for k, v in pesos.items()
    }
    total = sum(novos.values())
    return {k: round(v / total, 4) for k, v in novos.items()}


def taxa_suavizada(aprovados: int, total: int) -> float:
    """Taxa de aprovação com suavização de Laplace: (a + 1) / (n + 2).

    Com um único "não gostei", a taxa crua de uma categoria seria 0 % e ela
    sumiria das recomendações; suavizada, vale 0,33 e ainda tem chance.
    """
    return (aprovados + 1) / (total + 2)
