"""Contratos de entrada e saída da API.

Espelham a seção 6 do Documento de Visão: cada operação daquela lista tem um
schema aqui, com o mesmo vocabulário (peça, papel, formalidade, look, contexto).
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .services.cor import hex_para_hsv, hex_valido, nomear
from .services.taxonomia import POR_CHAVE, papel_coerente

Papel = Literal["superior", "inferior", "calcado", "sobreposicao", "acessorio"]


def _validar_hsv(valor: list[float]) -> list[float]:
    if len(valor) != 3:
        raise ValueError("cor_hsv deve ter exatamente 3 valores: matiz, saturação e valor")
    h, s, v = valor
    if not all(math.isfinite(x) for x in valor):
        raise ValueError("cor_hsv não aceita infinito nem NaN")
    if not 0 <= h <= 360:
        raise ValueError("matiz (1º valor) deve ficar entre 0 e 360")
    if not (0 <= s <= 1 and 0 <= v <= 1):
        raise ValueError("saturação e valor (2º e 3º) devem ficar entre 0 e 1")
    return [round(h % 360, 2), round(s, 4), round(v, 4)]


def _validar_hex(valor: str) -> str:
    if not hex_valido(valor):
        raise ValueError("use o formato #rrggbb")
    return "#" + valor.lstrip("#").lower()


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
    confianca_baixa: bool = False
    recorte: str | None = None        # data URL WebP da peça sem fundo


class PecaEntrada(BaseModel):
    """O que a tela de confirmação envia, já com as correções manuais."""
    categoria: str = Field(min_length=1, max_length=40)
    papel: Papel
    formalidade: int = Field(ge=1, le=5)
    cor_nome: str = Field(min_length=1, max_length=30)
    cor_hex: str
    cor_hsv: list[float] | None = None     # ausente: calculado a partir do hex
    neutra: bool | None = None             # ausente: decorre da cor
    temp_min: float = Field(default=0, ge=-30, le=60)
    temp_max: float = Field(default=45, ge=-30, le=60)
    resiste_chuva: bool = True
    atributos: dict[str, str] = {}
    imagem_path: str | None = Field(default=None, max_length=300)
    confianca: dict[str, float] = {}

    @field_validator("cor_hex")
    @classmethod
    def _hex(cls, valor: str) -> str:
        return _validar_hex(valor)

    @field_validator("cor_hsv")
    @classmethod
    def _hsv(cls, valor):
        return None if valor is None else _validar_hsv(valor)

    @field_validator("cor_nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return valor.strip().lower()

    @model_validator(mode="after")
    def _coerencia(self):
        if not papel_coerente(self.categoria, self.papel):
            esperado = POR_CHAVE[self.categoria].papel
            raise ValueError(
                f"a categoria '{self.categoria}' é do papel '{esperado}', não '{self.papel}'")
        if self.temp_min > self.temp_max:
            raise ValueError("temp_min não pode ser maior que temp_max")
        if self.cor_hsv is None:
            self.cor_hsv = _validar_hsv(list(hex_para_hsv(self.cor_hex)))
        if self.neutra is None:
            self.neutra = nomear(*self.cor_hsv)[1]
        return self


class PecaAtualizacao(BaseModel):
    categoria: str | None = Field(default=None, min_length=1, max_length=40)
    papel: Papel | None = None
    formalidade: int | None = Field(default=None, ge=1, le=5)
    cor_nome: str | None = Field(default=None, min_length=1, max_length=30)
    cor_hex: str | None = None
    disponivel: bool | None = None
    atributos: dict[str, str] | None = None

    @field_validator("cor_hex")
    @classmethod
    def _hex(cls, valor):
        return None if valor is None else _validar_hex(valor)

    @field_validator("cor_nome")
    @classmethod
    def _nome(cls, valor):
        return None if valor is None else valor.strip().lower()


class PecaSaida(PecaEntrada):
    id: str
    codigo: str
    disponivel: bool
    revisada: bool
    criado_em: str


# -------------------------------------------------------------- 6.4 contexto
class ContextoEntrada(BaseModel):
    # Todos opcionais: evento explícito, texto livre e inspiração se completam.
    # Sem nada, vale um passeio casual.
    evento: str | None = None
    texto: str | None = Field(default=None, max_length=300)
    estilo: str | None = None
    inspiracao: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    # informados manualmente quando a API de clima falha (RNF07)
    temperatura: float | None = Field(default=None, ge=-30, le=55)
    sensacao: float | None = Field(default=None, ge=-40, le=65)
    chuva_prob: float | None = Field(default=None, ge=0, le=1)


class ContextoSaida(BaseModel):
    id: str
    evento: str
    evento_rotulo: str = ""
    estilo: str | None = None
    formalidade_alvo: int
    temperatura: float | None
    sensacao: float | None
    chuva_prob: float | None
    clima_automatico: bool
    entendido: list[str] = []         # o que o texto livre significou para o motor


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
    titulo: str = ""
    resumo: str = ""
    explicacao: str
    salvo: bool = False
    aprovado: bool | None = None
    criado_em: str | None = None
    pecas: list[PecaDoLook]


class RecomendacaoSaida(BaseModel):
    contexto: ContextoSaida
    looks: list[LookSaida]
    avisos: list[str] = []


# ------------------------------------------------------------- 6.6 feedback
class FeedbackEntrada(BaseModel):
    look_id: str
    aprovado: bool


class FeedbackSaida(BaseModel):
    registrado: bool
    pesos: dict[str, float]


class SalvarLookEntrada(BaseModel):
    salvo: bool = True


# ------------------------------------------------------------------ perfil
class PerfilAtualizacao(BaseModel):
    nome: str = Field(min_length=1, max_length=80)

    @field_validator("nome")
    @classmethod
    def _limpar(cls, valor: str) -> str:
        limpo = " ".join(valor.split())
        if not limpo:
            raise ValueError("informe um nome")
        return limpo


class ConsentimentoEntrada(BaseModel):
    versao: str = Field(min_length=1, max_length=40)
    # A localização é uma finalidade separada e opcional: quem recusa continua
    # usando o app e informa a temperatura à mão.
    localizacao: bool = False


class ExclusaoContaEntrada(BaseModel):
    confirmacao: str
