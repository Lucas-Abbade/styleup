"""Taxonomia de vestuário masculino do StyleUp.

Este módulo é a fonte única de verdade sobre *quais* peças o sistema conhece e
*como* cada uma se comporta: papel no look, formalidade (escala 1-5 do
glossário), faixa de temperatura de conforto e resistência à chuva.

É deliberadamente um dicionário e não um modelo treinado. As regras de vestuário
mudam por revisão do consultor de imagem (seção 3.1 do Documento de Visão), não
por retreino, e precisam ser auditáveis pela banca.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PAPEIS = ("superior", "inferior", "calcado", "sobreposicao", "acessorio")
PAPEIS_OBRIGATORIOS = ("superior", "inferior", "calcado")


@dataclass(frozen=True)
class Categoria:
    chave: str
    rotulo: str            # como aparece na interface
    papel: str             # superior | inferior | calcado | sobreposicao | acessorio
    formalidade: int       # 1 esportiva ... 5 social
    temp_min: float        # abaixo disto a peça é desconfortável
    temp_max: float
    resiste_chuva: bool = True
    prompts: tuple[str, ...] = field(default_factory=tuple)  # descrições em inglês p/ o CLIP
    genero: str = "m"      # concordância do nome da cor: "camisa branca", "tênis branco"
    esportiva: bool = False     # serve para treino (evento "academia", estilo esportivo)
    urbana: bool = False        # repertório streetwear (estilo "urbano")
    denim: bool = False         # jeans azul funciona como neutro na harmonia de cores
    regiao: str | None = None   # só acessórios: evita dois itens no mesmo lugar do corpo
    folga_formalidade: int = 1  # acessórios versáteis (cinto, relógio) aceitam folga maior


# O CLIP foi treinado em inglês; os prompts ficam em inglês e o rótulo em
# português. Manter os dois lados no mesmo lugar evita divergência silenciosa.
#
# Faixas térmicas: o limite superior das calças e camisas foi alargado em relação
# à primeira versão. Em Cuiabá, 36 °C é dia comum e as pessoas vão trabalhar de
# calça; com o teto antigo (32 °C) o filtro rígido eliminava todas as partes de
# baixo aceitáveis para "trabalho" e a recomendação falhava. Desconforto com o
# calor é assunto da nota de clima, não motivo para não recomendar nada.
CATEGORIAS: tuple[Categoria, ...] = (
    # ------------------------------------------------------------- superior
    Categoria("camiseta", "Camiseta", "superior", 1, 18, 45,
              prompts=("a photo of a plain t-shirt", "a short sleeve cotton t-shirt"),
              genero="f", esportiva=True, urbana=True),
    Categoria("regata", "Regata", "superior", 1, 24, 45,
              prompts=("a photo of a tank top", "a sleeveless shirt"),
              genero="f", esportiva=True),
    Categoria("polo", "Camisa polo", "superior", 3, 18, 40,
              prompts=("a photo of a polo shirt", "a piqué polo shirt with collar"),
              genero="f"),
    Categoria("camisa-casual", "Camisa casual", "superior", 3, 14, 38,
              prompts=("a photo of a casual button-up shirt", "a denim or flannel shirt"),
              genero="f"),
    Categoria("camisa-social", "Camisa social", "superior", 5, 12, 38,
              prompts=("a photo of a formal dress shirt", "a white business shirt"),
              genero="f"),
    Categoria("moletom", "Moletom", "superior", 2, 5, 22,
              prompts=("a photo of a sweatshirt", "a hoodie"),
              esportiva=True, urbana=True),
    Categoria("sueter", "Suéter", "superior", 3, 2, 20,
              prompts=("a photo of a knitted sweater", "a wool pullover")),
    # ------------------------------------------------------------- inferior
    Categoria("bermuda", "Bermuda", "inferior", 1, 22, 45,
              prompts=("a photo of shorts", "casual bermuda shorts"),
              genero="f", esportiva=True),
    Categoria("calca-jeans", "Calça jeans", "inferior", 2, 8, 34,
              prompts=("a photo of blue jeans", "denim trousers"),
              genero="f", urbana=True, denim=True),
    Categoria("calca-sarja", "Calça de sarja", "inferior", 3, 8, 36,
              prompts=("a photo of chino trousers", "cotton twill pants"), genero="f"),
    Categoria("calca-social", "Calça social", "inferior", 5, 8, 36,
              prompts=("a photo of formal dress trousers", "suit pants"), genero="f"),
    Categoria("calca-moletom", "Calça de moletom", "inferior", 1, 5, 24,
              prompts=("a photo of sweatpants", "jogger pants"),
              genero="f", esportiva=True, urbana=True),
    # ------------------------------------------------------------- calçado
    Categoria("tenis", "Tênis", "calcado", 2, 0, 45,
              prompts=("a photo of sneakers", "casual running shoes"),
              esportiva=True, urbana=True),
    Categoria("tenis-casual", "Tênis casual", "calcado", 3, 0, 45,
              prompts=("a photo of minimalist leather sneakers", "white court sneakers"),
              urbana=True),
    Categoria("sapato-social", "Sapato social", "calcado", 5, 0, 40,
              prompts=("a photo of formal leather dress shoes", "oxford shoes")),
    Categoria("mocassim", "Mocassim", "calcado", 4, 0, 40,
              prompts=("a photo of loafers", "leather moccasin shoes")),
    Categoria("bota", "Bota", "calcado", 3, 0, 28,
              prompts=("a photo of leather boots", "chelsea boots"),
              genero="f", urbana=True),
    Categoria("chinelo", "Chinelo", "calcado", 1, 24, 45, resiste_chuva=False,
              prompts=("a photo of flip flops", "rubber sandals")),
    Categoria("sandalia", "Sandália", "calcado", 1, 22, 45, resiste_chuva=False,
              prompts=("a photo of open sandals", "leather sandals"), genero="f"),
    # --------------------------------------------------------- sobreposição
    Categoria("jaqueta-jeans", "Jaqueta jeans", "sobreposicao", 2, 8, 22,
              prompts=("a photo of a denim jacket",),
              genero="f", urbana=True, denim=True),
    Categoria("jaqueta-couro", "Jaqueta de couro", "sobreposicao", 3, 4, 20,
              prompts=("a photo of a leather jacket",), genero="f", urbana=True),
    Categoria("corta-vento", "Corta-vento", "sobreposicao", 2, 6, 24,
              prompts=("a photo of a windbreaker", "a nylon rain jacket"),
              esportiva=True, urbana=True),
    Categoria("blazer", "Blazer", "sobreposicao", 5, 8, 26,
              prompts=("a photo of a blazer", "a suit jacket")),
    Categoria("casaco", "Casaco", "sobreposicao", 3, -5, 16,
              prompts=("a photo of a winter coat", "a heavy overcoat")),
    # ------------------------------------------------------------ acessório
    # Sempre opcionais: o look existe sem eles. Entram depois da combinação
    # principal, no máximo um por região do corpo.
    Categoria("bone", "Boné", "acessorio", 1, 15, 45,
              prompts=("a photo of a baseball cap", "a cap hat"),
              esportiva=True, urbana=True, regiao="cabeca"),
    Categoria("gorro", "Gorro", "acessorio", 2, -10, 16,
              prompts=("a photo of a beanie", "a knitted winter hat"),
              urbana=True, regiao="cabeca"),
    Categoria("cinto", "Cinto", "acessorio", 4, -10, 45,
              prompts=("a photo of a leather belt", "a belt with a buckle"),
              regiao="cintura", folga_formalidade=2),
    Categoria("relogio", "Relógio", "acessorio", 3, -10, 45,
              prompts=("a photo of a wristwatch", "a watch"),
              regiao="pulso", folga_formalidade=2),
    Categoria("oculos", "Óculos de sol", "acessorio", 2, 18, 45, resiste_chuva=False,
              prompts=("a photo of sunglasses",),
              urbana=True, regiao="rosto", folga_formalidade=2),
    Categoria("cachecol", "Cachecol", "acessorio", 3, -10, 15,
              prompts=("a photo of a scarf", "a wool scarf"),
              regiao="pescoco", folga_formalidade=2),
    Categoria("mochila", "Mochila", "acessorio", 2, -10, 45,
              prompts=("a photo of a backpack",),
              genero="f", esportiva=True, urbana=True, regiao="costas"),
)

POR_CHAVE: dict[str, Categoria] = {c.chave: c for c in CATEGORIAS}

# ------------------------------------------------------------------ eventos
# Mapeia o tipo de evento escolhido pelo usuário para a formalidade esperada.
#
# "preferidas" e "vetadas" existem porque a formalidade sozinha não distingue
# eventos: "em casa" e "academia" valem 1, mas chinelo serve a um e não ao outro.
DRESS_CODE: dict[str, dict] = {
    "casa":      {"rotulo": "Em casa",               "formalidade": 1,
                  "preferidas": ("camiseta", "regata", "bermuda", "calca-moletom",
                                 "moletom", "chinelo"),
                  "vetadas": ()},
    "casual":    {"rotulo": "Passeio casual",        "formalidade": 2,
                  "preferidas": (), "vetadas": ()},
    "academia":  {"rotulo": "Academia",              "formalidade": 1,
                  "preferidas": ("camiseta", "regata", "bermuda", "calca-moletom",
                                 "tenis", "moletom", "corta-vento", "bone", "mochila"),
                  "vetadas": ("chinelo", "sandalia", "calca-jeans", "calca-sarja",
                              "polo", "camisa-casual", "bota", "mocassim",
                              "jaqueta-jeans", "jaqueta-couro", "cinto", "oculos",
                              "cachecol", "relogio")},
    "praia":     {"rotulo": "Praia ou piscina",      "formalidade": 1,
                  "preferidas": ("regata", "camiseta", "bermuda", "chinelo",
                                 "sandalia", "bone", "oculos"),
                  "vetadas": ("calca-moletom", "moletom", "cinto", "relogio")},
    "faculdade": {"rotulo": "Faculdade",             "formalidade": 2,
                  "preferidas": (), "vetadas": ("chinelo",)},
    "trabalho":  {"rotulo": "Trabalho",              "formalidade": 3,
                  "preferidas": (), "vetadas": ("calca-moletom", "moletom", "bone")},
    "balada":    {"rotulo": "Rolê ou balada",        "formalidade": 3,
                  "preferidas": ("camisa-casual", "polo", "jaqueta-couro",
                                 "jaqueta-jeans", "calca-jeans", "calca-sarja",
                                 "tenis-casual", "bota"),
                  "vetadas": ("calca-moletom", "moletom", "mochila")},
    "reuniao":   {"rotulo": "Reunião ou entrevista", "formalidade": 4,
                  "preferidas": (), "vetadas": ("bone", "mochila")},
    "jantar":    {"rotulo": "Jantar ou evento",      "formalidade": 4,
                  "preferidas": (), "vetadas": ("bone", "mochila")},
    "formal":    {"rotulo": "Evento formal",         "formalidade": 5,
                  "preferidas": ("camisa-social", "calca-social", "sapato-social",
                                 "blazer"),
                  "vetadas": ("bone", "mochila", "oculos")},
}

EVENTO_PADRAO = "casual"

# ------------------------------------------------------------------ estilos
# Diretriz opcional pedida pelo usuário ("all black", "minimalista"). Não é
# filtro: entra no critério de estilo do score, então o motor ainda recomenda
# quando o guarda-roupa não tem o repertório pedido.
ESTILOS: dict[str, dict] = {
    "minimalista":   {"rotulo": "Minimalista",   "descricao": "cores neutras e peças lisas"},
    "all-black":     {"rotulo": "All black",     "descricao": "tudo em preto"},
    "esportivo":     {"rotulo": "Esportivo",     "descricao": "peças de treino e conforto"},
    "urbano":        {"rotulo": "Urbano",        "descricao": "repertório streetwear"},
    "classico":      {"rotulo": "Clássico",      "descricao": "peças alinhadas e discretas"},
    "colorido":      {"rotulo": "Colorido",      "descricao": "pelo menos um ponto de cor"},
    "terroso":       {"rotulo": "Tons terrosos", "descricao": "marrom, bege, cáqui e oliva"},
    "monocromatico": {"rotulo": "Monocromático", "descricao": "uma única família de cor"},
    "claro":         {"rotulo": "Tons claros",   "descricao": "paleta clara"},
    "escuro":        {"rotulo": "Tons escuros",  "descricao": "paleta escura"},
}

# ------------------------------------------------------------- inspirações
# Atalhos da tela "Gerador de Looks". Cada um é só um contexto pré-preenchido;
# o motor não tem caminho especial para eles.
INSPIRACOES: tuple[dict, ...] = (
    {"chave": "trabalho-faculdade", "rotulo": "Trabalho / Faculdade", "icone": "maleta",
     "evento": "trabalho"},
    {"chave": "role-balada", "rotulo": "Rolê / Balada", "icone": "festa",
     "evento": "balada"},
    {"chave": "dias-frios", "rotulo": "Dias frios", "icone": "frio",
     "temperatura": 12.0},
    {"chave": "verao", "rotulo": "Verão", "icone": "verao",
     "temperatura": 32.0},
    {"chave": "minimalista", "rotulo": "Minimalista", "icone": "cabide",
     "estilo": "minimalista"},
    {"chave": "esportivo", "rotulo": "Esportivo", "icone": "camiseta",
     "evento": "academia", "estilo": "esportivo"},
)
INSPIRACAO_POR_CHAVE: dict[str, dict] = {i["chave"]: i for i in INSPIRACOES}

# Atributos secundários que o modelo tenta inferir junto da categoria.
ATRIBUTOS = {
    "manga":   {"curta": ("short sleeve",), "longa": ("long sleeve",)},
    "estampa": {"lisa": ("solid color plain fabric",),
                "listrada": ("striped pattern",),
                "estampada": ("printed graphic pattern",),
                "xadrez": ("plaid checkered pattern",)},
}

# Rótulo do nível de formalidade, usado no título do look e no relatório de
# acurácia (coluna "estilo" do CSV de avaliação).
NIVEL_FORMALIDADE = {1: "Esportivo", 2: "Casual", 3: "Casual arrumado",
                     4: "Social", 5: "Formal"}


def categorias_do_papel(papel: str) -> list[Categoria]:
    return [c for c in CATEGORIAS if c.papel == papel]


def papel_coerente(categoria: str, papel: str) -> bool:
    """Uma camiseta não pode ser cadastrada como calçado. Categoria fora da
    taxonomia (texto livre antigo) é aceita com qualquer papel conhecido."""
    cat = POR_CHAVE.get(categoria)
    return papel in PAPEIS if cat is None else cat.papel == papel
