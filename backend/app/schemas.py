"""Contratos de entrada e saída da API.

Espelham a seção 6 do Documento de Visão: cada operação daquela lista tem um
schema aqui, com o mesmo vocabulário (peça, papel, formalidade, look, contexto).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Papel = Literal["superior", "inferior", "calcado", "sobreposicao"]


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


class PecaEntrada(BaseModel):
    """O que a tela de confirmação envia, já com as correções manuais."""
    categoria: str
    papel: Papel
    formalidade: int = Field(ge=1, le=5)
    cor_nome: str
    cor_hex: str
    cor_hsv: list[float]
    neutra: bool = False
    temp_min: float = 0
    temp_max: float = 45
    resiste_chuva: bool = True
    atributos: dict[str, str] = {}
    imagem_path: str | None = None
    confianca: dict[str, float] = {}


class PecaAtualizacao(BaseModel):
    categoria: str | None = None
    papel: Papel | None = None
    formalidade: int | None = Field(default=None, ge=1, le=5)
    cor_nome: str | None = None
    cor_hex: str | None = None
    disponivel: bool | None = None
    atributos: dict[str, str] | None = None


class PecaSaida(PecaEntrada):
    id: str
    codigo: str
    disponivel: bool
    revisada: bool
    criado_em: str


# -------------------------------------------------------------- 6.4 contexto
class ContextoEntrada(BaseModel):
    evento: str
    latitude: float | None = None
    longitude: float | None = None
    # informados manualmente quando a API de clima falha (RNF07)
    temperatura: float | None = None
    sensacao: float | None = None
    chuva_prob: float | None = Field(default=None, ge=0, le=1)


class ContextoSaida(BaseModel):
    id: str
    evento: str
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
    look_id: str
    aprovado: bool


class FeedbackSaida(BaseModel):
    registrado: bool
    pesos: dict[str, float]
