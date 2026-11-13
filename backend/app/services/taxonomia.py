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


@dataclass(frozen=True)
class Categoria:
    chave: str
    rotulo: str            # como aparece na interface
    papel: str             # superior | inferior | calcado | sobreposicao
    formalidade: int       # 1 esportiva ... 5 social
    temp_min: float        # abaixo disto a peça é desconfortável
    temp_max: float
    resiste_chuva: bool = True
    prompts: tuple[str, ...] = field(default_factory=tuple)  # descrições em inglês p/ o CLIP
    genero: str = "m"      # concordância do nome da cor: "camisa branca", "tênis branco"


# O CLIP foi treinado em inglês; os prompts ficam em inglês e o rótulo em
# português. Manter os dois lados no mesmo lugar evita divergência silenciosa.
CATEGORIAS: tuple[Categoria, ...] = (
    # ------------------------------------------------------------- superior
    Categoria("camiseta", "Camiseta", "superior", 1, 18, 45,
              prompts=("a photo of a plain t-shirt", "a short sleeve cotton t-shirt"), genero="f"),
    Categoria("regata", "Regata", "superior", 1, 24, 45,
              prompts=("a photo of a tank top", "a sleeveless shirt"), genero="f"),
    Categoria("polo", "Camisa polo", "superior", 3, 18, 40,
              prompts=("a photo of a polo shirt", "a piqué polo shirt with collar")),
    Categoria("camisa-casual", "Camisa casual", "superior", 3, 14, 38,
              prompts=("a photo of a casual button-up shirt", "a denim or flannel shirt"), genero="f"),
    Categoria("camisa-social", "Camisa social", "superior", 5, 12, 35,
              prompts=("a photo of a formal dress shirt", "a white business shirt"), genero="f"),
    Categoria("moletom", "Moletom", "superior", 2, 5, 22,
              prompts=("a photo of a sweatshirt", "a hoodie")),
    Categoria("sueter", "Suéter", "superior", 3, 2, 20,
              prompts=("a photo of a knitted sweater", "a wool pullover")),
    # ------------------------------------------------------------- inferior
    Categoria("bermuda", "Bermuda", "inferior", 1, 22, 45,
              prompts=("a photo of shorts", "casual bermuda shorts"), genero="f"),
    Categoria("calca-jeans", "Calça jeans", "inferior", 2, 8, 32,
              prompts=("a photo of blue jeans", "denim trousers"), genero="f"),
    Categoria("calca-sarja", "Calça de sarja", "inferior", 3, 8, 32,
              prompts=("a photo of chino trousers", "cotton twill pants"), genero="f"),
    Categoria("calca-social", "Calça social", "inferior", 5, 8, 32,
              prompts=("a photo of formal dress trousers", "suit pants"), genero="f"),
    Categoria("calca-moletom", "Calça de moletom", "inferior", 1, 5, 24,
              prompts=("a photo of sweatpants", "jogger pants"), genero="f"),
    # ------------------------------------------------------------- calçado
    Categoria("tenis", "Tênis", "calcado", 2, 0, 45,
              prompts=("a photo of sneakers", "casual running shoes")),
    Categoria("tenis-casual", "Tênis casual", "calcado", 3, 0, 45,
              prompts=("a photo of minimalist leather sneakers", "white court sneakers")),
    Categoria("sapato-social", "Sapato social", "calcado", 5, 0, 40,
              prompts=("a photo of formal leather dress shoes", "oxford shoes")),
    Categoria("mocassim", "Mocassim", "calcado", 4, 0, 40,
              prompts=("a photo of loafers", "leather moccasin shoes")),
    Categoria("bota", "Bota", "calcado", 3, 0, 28,
              prompts=("a photo of leather boots", "chelsea boots"), genero="f"),
    Categoria("chinelo", "Chinelo", "calcado", 1, 24, 45, resiste_chuva=False,
              prompts=("a photo of flip flops", "rubber sandals")),
    Categoria("sandalia", "Sandália", "calcado", 1, 22, 45, resiste_chuva=False,
              prompts=("a photo of open sandals", "leather sandals"), genero="f"),
    # --------------------------------------------------------- sobreposição
    Categoria("jaqueta-jeans", "Jaqueta jeans", "sobreposicao", 2, 8, 22,
              prompts=("a photo of a denim jacket",), genero="f"),
    Categoria("jaqueta-couro", "Jaqueta de couro", "sobreposicao", 3, 4, 20,
              prompts=("a photo of a leather jacket",), genero="f"),
    Categoria("corta-vento", "Corta-vento", "sobreposicao", 2, 6, 24,
              prompts=("a photo of a windbreaker", "a nylon rain jacket")),
    Categoria("blazer", "Blazer", "sobreposicao", 5, 8, 24,
              prompts=("a photo of a blazer", "a suit jacket")),
    Categoria("casaco", "Casaco", "sobreposicao", 3, -5, 16,
              prompts=("a photo of a winter coat", "a heavy overcoat")),
)

POR_CHAVE: dict[str, Categoria] = {c.chave: c for c in CATEGORIAS}

PAPEIS_OBRIGATORIOS = ("superior", "inferior", "calcado")

# ------------------------------------------------------------------ eventos
# Mapeia o tipo de evento escolhido pelo usuário para a formalidade esperada.
DRESS_CODE: dict[str, dict] = {
    "casa":      {"rotulo": "Em casa",              "formalidade": 1},
    "casual":    {"rotulo": "Passeio casual",       "formalidade": 2},
    "academia":  {"rotulo": "Academia",             "formalidade": 1},
    "faculdade": {"rotulo": "Faculdade",            "formalidade": 2},
    "trabalho":  {"rotulo": "Trabalho",             "formalidade": 3},
    "reuniao":   {"rotulo": "Reunião ou entrevista","formalidade": 4},
    "jantar":    {"rotulo": "Jantar ou evento",     "formalidade": 4},
    "formal":    {"rotulo": "Evento formal",        "formalidade": 5},
}

# Atributos secundários que o modelo tenta inferir junto da categoria.
ATRIBUTOS = {
    "manga":   {"curta": ("short sleeve",), "longa": ("long sleeve",)},
    "estampa": {"lisa": ("solid color plain fabric",),
                "listrada": ("striped pattern",),
                "estampada": ("printed graphic pattern",),
                "xadrez": ("plaid checkered pattern",)},
}


def categorias_do_papel(papel: str) -> list[Categoria]:
    return [c for c in CATEGORIAS if c.papel == papel]
