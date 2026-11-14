"""Validação do JWT do Supabase e limites do modo demonstração."""

from __future__ import annotations

import dataclasses
import time

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app import auth
from app.erros import ErroAPI

SEGREDO = "segredo-de-teste-com-mais-de-32-caracteres!!"
URL = "https://exemplo.supabase.co"


@pytest.fixture
def supabase_real(monkeypatch):
    """Simula um projeto configurado (HS256): o modo demonstração desliga."""
    cfg = dataclasses.replace(auth.config, supabase_url=URL, supabase_anon_key="anon",
                              supabase_jwt_secret=SEGREDO, _modo_demo="auto")
    monkeypatch.setattr(auth, "config", cfg)
    return cfg


def _token(**mudancas):
    dados = {"sub": "u-1", "email": "a@b.c", "aud": "authenticated",
             "iss": f"{URL}/auth/v1", "exp": int(time.time()) + 600, **mudancas}
    return jwt.encode(dados, mudancas.pop("_chave", SEGREDO), algorithm="HS256")


def _entrar(token):
    return auth.usuario_atual(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))


def test_token_valido(supabase_real):
    usuario = _entrar(_token())
    assert (usuario.id, usuario.email, usuario.demo) == ("u-1", "a@b.c", False)


@pytest.mark.parametrize("mudancas, codigo", [
    ({"exp": int(time.time()) - 10}, "sessao_expirada"),
    ({"aud": "anon"}, "token_invalido"),
    ({"iss": "https://outro.supabase.co/auth/v1"}, "token_invalido"),
    ({"sub": ""}, "token_invalido"),
])
def test_tokens_recusados(supabase_real, mudancas, codigo):
    with pytest.raises(ErroAPI) as exc:
        _entrar(_token(**mudancas))
    assert exc.value.status == 401 and exc.value.codigo == codigo


def test_assinatura_errada_e_lixo_nao_vazam_detalhes(supabase_real):
    falso = jwt.encode({"sub": "u", "aud": "authenticated", "iss": f"{URL}/auth/v1",
                        "exp": int(time.time()) + 600}, "outro-segredo-qualquer-bem-comprido-1234",
                       algorithm="HS256")
    for token in (falso, "nao.e.jwt", "lixo"):
        with pytest.raises(ErroAPI) as exc:
            _entrar(token)
        assert exc.value.codigo == "token_invalido"
        assert "Signature" not in exc.value.mensagem and "segment" not in exc.value.mensagem


def test_algoritmo_none_e_recusado(supabase_real):
    sem_assinatura = jwt.encode({"sub": "u", "aud": "authenticated"}, None, algorithm="none")
    with pytest.raises(ErroAPI):
        _entrar(sem_assinatura)


def test_token_demo_so_vale_no_modo_demonstracao(supabase_real):
    with pytest.raises(ErroAPI):
        _entrar("demo")
    with pytest.raises(ErroAPI):
        _entrar("demo:ana")


def test_modo_demo_nunca_liga_em_producao():
    cfg = dataclasses.replace(auth.config, ambiente="producao", _modo_demo="true",
                              supabase_url="", supabase_anon_key="")
    assert cfg.modo_demo is False


def test_usuarios_demo_sao_isolados_e_estaveis():
    assert _entrar("demo:ana").id == _entrar("demo:ana").id != _entrar("demo:bruno").id
    assert _entrar("demo").demo is True


def test_sem_cabecalho():
    with pytest.raises(ErroAPI) as exc:
        auth.usuario_atual(None)
    assert exc.value.status == 401


def test_nenhum_print_de_depuracao_no_codigo():
    """Fase 1, item 2: havia um print("DEBUG url...") em auth.py."""
    from pathlib import Path
    for arquivo in Path(auth.__file__).parent.rglob("*.py"):
        assert "print(" not in arquivo.read_text(encoding="utf-8"), arquivo
