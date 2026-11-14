"""Configuração lida do ambiente. Nenhum segredo no código."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _bool(nome: str, padrao: str) -> bool:
    return os.getenv(nome, padrao).strip().lower() in ("1", "true", "sim", "yes")


@dataclass(frozen=True)
class Config:
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "").strip().rstrip("/"))
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "").strip())
    # Segredo usado pelo Supabase para assinar o JWT (Settings > API > JWT Secret).
    # Só é necessário em projetos que ainda assinam com HS256; projetos com
    # chaves assimétricas (ES256/RS256) são validados pelo JWKS público.
    supabase_jwt_secret: str = field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", "").strip())

    modelo_clip: str = field(
        default_factory=lambda: os.getenv("MODELO_CLIP", "patrickjohncyh/fashion-clip"))
    usar_llm: bool = field(default_factory=lambda: _bool("USAR_LLM", "false"))

    origens_permitidas: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.getenv(
                "ORIGENS_PERMITIDAS", "http://localhost:5173"
            ).split(",") if o.strip()
        ))

    ambiente: str = field(default_factory=lambda: os.getenv("AMBIENTE", "desenvolvimento"))

    # Versão do termo de consentimento em vigor. Mudou o texto ou a finalidade?
    # Mude a versão: todo usuário volta a ser consultado (LGPD, art. 8º, § 6º).
    versao_termo: str = field(
        default_factory=lambda: os.getenv("VERSAO_TERMO", "2026-11-v1"))
    exigir_consentimento: bool = field(
        default_factory=lambda: _bool("EXIGIR_CONSENTIMENTO", "true"))

    # Carrega rembg e FashionCLIP na subida da API (em segundo plano).
    aquecer_modelos: bool = field(default_factory=lambda: _bool("AQUECER_MODELOS", "true"))

    # Quantos feedbacks recentes alimentam a preferência por categoria.
    janela_feedback: int = field(
        default_factory=lambda: int(os.getenv("JANELA_FEEDBACK", "200")))

    _modo_demo: str = field(default_factory=lambda: os.getenv("MODO_DEMO", "auto").lower())

    @property
    def configurado(self) -> bool:
        """Supabase utilizável: URL e chave pública. O JWT secret é opcional
        (só projetos HS256 precisam dele)."""
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def producao(self) -> bool:
        return self.ambiente.lower() in ("producao", "produção", "production", "prod")

    @property
    def modo_demo(self) -> bool:
        """Dados em memória e login fictício, para desenvolver e apresentar sem
        Supabase. Nunca liga em produção, nem por engano de configuração."""
        if self.producao:
            return False
        if self._modo_demo in ("1", "true", "sim", "yes"):
            return True
        if self._modo_demo in ("0", "false", "nao", "não", "no"):
            return False
        return not self.configurado


@lru_cache(maxsize=1)
def _carregar() -> Config:
    return Config()


config = _carregar()
