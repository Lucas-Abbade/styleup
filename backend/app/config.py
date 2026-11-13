"""Configuração lida do ambiente. Nenhum segredo no código."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Config:
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", ""))
    # Segredo usado pelo Supabase para assinar o JWT (Settings > API > JWT Secret).
    supabase_jwt_secret: str = field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", ""))

    modelo_clip: str = field(
        default_factory=lambda: os.getenv("MODELO_CLIP", "patrickjohncyh/fashion-clip"))
    usar_llm: bool = field(
        default_factory=lambda: os.getenv("USAR_LLM", "false").lower() == "true")

    origens_permitidas: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.getenv(
                "ORIGENS_PERMITIDAS", "http://localhost:5173"
            ).split(",") if o.strip()
        ))

    ambiente: str = field(default_factory=lambda: os.getenv("AMBIENTE", "desenvolvimento"))

    @property
    def configurado(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key
                    and self.supabase_jwt_secret)


@lru_cache(maxsize=1)
def _carregar() -> Config:
    return Config()


config = _carregar()
