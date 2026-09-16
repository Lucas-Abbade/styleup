"""Testes da validação do JWT.

O caminho de produção da autenticação não era exercitado: os testes de API rodam
em modo demonstração, onde `usuario_atual` devolve o usuário fixo sem olhar o
token. Aqui geramos JWTs de verdade com a mesma biblioteca que o Supabase usa e
conferimos cada recusa.
"""

from __future__ import annotations

import time

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import config as modulo_config
from app.auth import USUARIO_DEMO_ID, usuario_atual

SEGREDO = "segredo-de-teste-do-supabase-com-32-bytes-ou-mais"


def credencial(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def gerar(payload: dict, segredo: str = SEGREDO, algoritmo: str = "HS256") -> str:
    return jwt.encode(payload, segredo, algorithm=algoritmo)


def payload_valido(**extra) -> dict:
    agora = int(time.time())
    return {
        "sub": "11111111-1111-4111-8111-111111111111",
        "email": "ana@exemplo.com",
        "aud": "authenticated",
        "iat": agora,
        "exp": agora + 3600,
        **extra,
    }


@pytest.fixture
def modo_producao(monkeypatch):
    monkeypatch.setenv("MODO_DEMO", "false")
    monkeypatch.setenv("SUPABASE_URL", "https://projeto.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "chave")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SEGREDO)
    modulo_config.recarregar()
    yield
    monkeypatch.undo()
    modulo_config.recarregar()


# ------------------------------------------------------------ demonstração
def test_demonstracao_dispensa_token():
    """Sem credenciais, a API responde como o usuário de exemplo."""
    assert modulo_config.config.modo_demo is True
    usuario = usuario_atual(None)
    assert usuario.id == USUARIO_DEMO_ID
    assert usuario.token is None


def test_demonstracao_ignora_token_invalido():
    usuario = usuario_atual(credencial("isto-nao-e-um-jwt"))
    assert usuario.id == USUARIO_DEMO_ID


# ------------------------------------------------------------- produção
def test_token_valido_e_aceito(modo_producao):
    usuario = usuario_atual(credencial(gerar(payload_valido())))
    assert usuario.id == "11111111-1111-4111-8111-111111111111"
    assert usuario.email == "ana@exemplo.com"
    assert usuario.token is not None       # repassado ao PostgREST para a RLS


def test_sem_cabecalho_e_401(modo_producao):
    with pytest.raises(HTTPException) as exc:
        usuario_atual(None)
    assert exc.value.status_code == 401
    assert "Authorization" in exc.value.detail


def test_assinatura_de_outro_segredo_e_recusada(modo_producao):
    """O caso que importa: token forjado por quem não tem o segredo."""
    forjado = gerar(payload_valido(), segredo="segredo-do-atacante-tambem-longo-o-bastante")
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial(forjado))
    assert exc.value.status_code == 401


def test_token_expirado_tem_mensagem_propria(modo_producao):
    """A tela precisa distinguir sessão vencida de token inválido."""
    agora = int(time.time())
    vencido = gerar(payload_valido(iat=agora - 7200, exp=agora - 3600))
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial(vencido))
    assert exc.value.status_code == 401
    assert "expirada" in exc.value.detail.lower()


def test_audiencia_errada_e_recusada(modo_producao):
    """`aud` separa token de usuário de token de serviço."""
    outro_publico = gerar(payload_valido(aud="service_role"))
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial(outro_publico))
    assert exc.value.status_code == 401


def test_token_sem_sub_e_recusado(modo_producao):
    """Sem `sub` não há `auth.uid()`, e a RLS não teria contra o que comparar."""
    sem_sub = gerar({k: v for k, v in payload_valido().items() if k != "sub"})
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial(sem_sub))
    assert exc.value.status_code == 401
    assert "identificação" in exc.value.detail


def test_token_sem_assinatura_e_recusado(modo_producao):
    """alg=none é o ataque clássico contra validação de JWT mal feita."""
    sem_assinatura = jwt.encode(payload_valido(), key="", algorithm="none")
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial(sem_assinatura))
    assert exc.value.status_code == 401


def test_texto_qualquer_no_lugar_do_token_e_recusado(modo_producao):
    with pytest.raises(HTTPException) as exc:
        usuario_atual(credencial("nem-parece-um-jwt"))
    assert exc.value.status_code == 401
