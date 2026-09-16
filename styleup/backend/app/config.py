"""Configuração lida do ambiente. Nenhum segredo no código."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(nome: str, padrao: bool = False) -> bool:
    return os.getenv(nome, str(padrao)).strip().lower() in ("1", "true", "sim", "yes")


@dataclass
class Config:
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", ""))
    # Segredo usado pelo Supabase para assinar o JWT (Settings > API > JWT Secret).
    supabase_jwt_secret: str = field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", ""))

    # Força o modo demonstração mesmo com o Supabase configurado. Útil para
    # desenvolver o frontend sem sujar os dados reais.
    forcar_demo: bool = field(default_factory=lambda: _bool("MODO_DEMO"))

    modelo_clip: str = field(
        default_factory=lambda: os.getenv("MODELO_CLIP", "patrickjohncyh/fashion-clip"))
    usar_llm: bool = field(default_factory=lambda: _bool("USAR_LLM"))

    origens_permitidas: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.getenv(
                "ORIGENS_PERMITIDAS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",") if o.strip()
        ))

    ambiente: str = field(default_factory=lambda: os.getenv("AMBIENTE", "desenvolvimento"))

    @property
    def supabase_configurado(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key
                    and self.supabase_jwt_secret)

    @property
    def modo_demo(self) -> bool:
        """Sem credenciais, a API roda em memória em vez de recusar tudo.

        Esta é a decisão que faz `uvicorn app.main:app` funcionar em qualquer
        máquina recém-clonada. O modo fica visível em `/saude` e no log de
        inicialização, para que ninguém confunda demonstração com produção.
        """
        return self.forcar_demo or not self.supabase_configurado


# Instância única, criada na importação do módulo.
config = Config()


def recarregar() -> Config:
    """Relê o ambiente **no mesmo objeto** `config`.

    Isto não é detalhe de estilo: metade dos módulos faz `from .config import
    config`, o que copia a referência no momento da importação. Trocar a variável
    global aqui deixaria todos eles apontando para a configuração antiga — os
    testes passariam e a aplicação leria valores obsoletos. Mutar em vigor é o
    que mantém as duas visões coerentes.
    """
    novo = Config()
    for campo in novo.__dataclass_fields__:
        setattr(config, campo, getattr(novo, campo))
    return config
