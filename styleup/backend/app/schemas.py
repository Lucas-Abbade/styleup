"""Contratos de entrada e saída da API.

Espelham a seção 6 do Documento de Visão: cada operação daquela lista tem um
schema aqui, com o mesmo vocabulário (peça, papel, formalidade, look, contexto).

Os `response_model` das rotas usam estes tipos, então um campo que o repositório
deixar de devolver falha na validação em vez de chegar ao frontend como `null`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Papel = Literal["superior", "inferior", "calcado", "sobreposicao"]

# Entradas recusam campo desconhecido. Um `cor_hex` grafado como `corHex` passava
# silenciosamente e a peça era gravada sem cor; agora a requisição falha com 422
# apontando o campo. Saídas ignoram extras, porque o repositório devolve colunas
# de controle (usuario_id, confianca) que não pertencem ao contrato público.
ENTRADA = ConfigDict(extra="forbid", str_strip_whitespace=True)
SAIDA = ConfigDict(extra="ignore")


# --------------------------------------------------------------- 6.2 análise
class AnaliseFoto(BaseModel):
    """Resultado da análise automática, antes da confirmação do usuário."""
    categoria: str
    rotulo: str
    papel: Papel
    formalidade: int = Field(ge=1, le=5)
    temp_min: float
    temp_max: float
    resiste_chuva: bool
    atributos: dict[str, str] = {}
    cor_nome: str
    cor_hex: str
    cor_hsv: list[float]
    neutra: bool
    confianca: dict[str, float] = {}
    # False quando o modelo de visão não está instalado: a cor é real, mas a
    # categoria é um palpite e a tela precisa pedir confirmação com mais ênfase.
    modelo_disponivel: bool = True
    aviso: str | None = None


class PecaEntrada(BaseModel):
    """O que a tela de confirmação envia, já com as correções manuais."""

    model_config = ENTRADA

    categoria: str = Field(min_length=1, max_length=40)
    papel: Papel
    formalidade: int = Field(ge=1, le=5)
    cor_nome: str = Field(min_length=1, max_length=40)
    # #rrggbb: o valor vai direto para `style.background` no frontend, então um
    # texto livre aqui seria injeção de CSS
    cor_hex: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    cor_hsv: list[float] = Field(min_length=3, max_length=3)
    neutra: bool = False
    temp_min: float = Field(default=0, ge=-40, le=60)
    temp_max: float = Field(default=45, ge=-40, le=60)
    resiste_chuva: bool = True
    atributos: dict[str, str] = {}
    imagem_path: str | None = Field(default=None, max_length=512)
    confianca: dict[str, float] = {}

    @model_validator(mode="after")
    def faixa_termica_coerente(self):
        """`temp_min` acima de `temp_max` deixaria a peça fora de todo filtro.

        Nenhuma restrição de campo isolado pega isso, e a peça entraria no acervo
        para nunca ser recomendada — falha silenciosa, difícil de diagnosticar
        pela tela.
        """
        if self.temp_min > self.temp_max:
            raise ValueError(
                "temp_min não pode ser maior que temp_max")
        return self


class PecaAtualizacao(BaseModel):
    model_config = ENTRADA

    categoria: str | None = Field(default=None, min_length=1, max_length=40)
    papel: Papel | None = None
    formalidade: int | None = Field(default=None, ge=1, le=5)
    cor_nome: str | None = Field(default=None, min_length=1, max_length=40)
    cor_hex: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    disponivel: bool | None = None
    atributos: dict[str, str] | None = None


class PecaSaida(PecaEntrada):
    model_config = SAIDA

    id: str
    codigo: str
    rotulo: str
    disponivel: bool
    revisada: bool
    criado_em: str


# -------------------------------------------------------------- 6.4 contexto
class ContextoEntrada(BaseModel):
    model_config = ENTRADA

    evento: str = Field(min_length=1, max_length=40)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    # informados manualmente quando a API de clima falha ou o usuário nega a
    # localização (RNF07)
    temperatura: float | None = Field(default=None, ge=-30, le=60)
    sensacao: float | None = Field(default=None, ge=-30, le=60)
    chuva_prob: float | None = Field(default=None, ge=0, le=1)


class ContextoSaida(BaseModel):
    id: str
    evento: str
    rotulo_evento: str
    formalidade_alvo: int
    temperatura: float | None
    sensacao: float | None
    chuva_prob: float | None
    clima_automatico: bool


# --------------------------------------------------------- 6.5 recomendação
class PecaDoLook(BaseModel):
    id: str
    codigo: str
    papel: Papel
    categoria: str
    rotulo: str
    cor_nome: str
    cor_hex: str
    imagem_path: str | None


class LookSaida(BaseModel):
    id: str
    posicao: int
    score: float
    parcelas: dict[str, float]
    explicacao: str
    pecas: list[PecaDoLook]


class RecomendacaoSaida(BaseModel):
    contexto: ContextoSaida
    looks: list[LookSaida]


# ------------------------------------------------------------- 6.6 feedback
class FeedbackEntrada(BaseModel):
    model_config = ENTRADA

    look_id: str = Field(min_length=1, max_length=64)
    aprovado: bool


class FeedbackSaida(BaseModel):
    registrado: bool
    pesos: dict[str, float]
