"""Repositório do Supabase, contra um cliente simulado (sem rede).

O que importa provar aqui é o que a fase 1 pediu: cada requisição tem o SEU
cliente, com o token do SEU usuário, no banco e no Storage — e nenhuma falha é
engolida em silêncio.
"""

from __future__ import annotations

import dataclasses
import threading

import httpx
import pytest
from postgrest.exceptions import APIError

from app.auth import Usuario
from app.erros import ErroAPI
from app.repositorio import supabase as modulo
from app.repositorio.supabase import RepositorioSupabase, criar_cliente


@pytest.fixture
def configurado(monkeypatch):
    cfg = dataclasses.replace(
        modulo.config, supabase_url="https://exemplo.supabase.co",
        supabase_anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.x")
    monkeypatch.setattr(modulo, "config", cfg)


def usuario(nome: str) -> Usuario:
    return Usuario(id=f"uid-{nome}", email=f"{nome}@t.dev", token=f"jwt-{nome}")


# ------------------------------------------------------ cliente por requisição
def test_banco_e_storage_levam_o_token_do_usuario(configurado):
    """`postgrest.auth(token)` autenticava só o PostgREST: o Storage saía anônimo."""
    cliente = criar_cliente(usuario("ana"))
    assert cliente.postgrest.session.headers["authorization"] == "Bearer jwt-ana"
    sessao = getattr(cliente.storage, "session", None) or cliente.storage._client
    assert sessao.headers["authorization"] == "Bearer jwt-ana"
    assert cliente.postgrest.session.headers["apikey"].startswith("eyJ")


def test_clientes_nao_sao_compartilhados_entre_requisicoes(configurado):
    """O cliente global fazia requisições simultâneas trocarem de token."""
    resultados: dict[str, str] = {}
    barreira = threading.Barrier(8)

    def requisicao(nome: str) -> None:
        repo = RepositorioSupabase(usuario(nome))
        barreira.wait()                               # todas "ao mesmo tempo"
        resultados[nome] = repo.cliente.postgrest.session.headers["authorization"]
        repo.fechar()

    nomes = [f"u{i}" for i in range(8)]
    threads = [threading.Thread(target=requisicao, args=(n,)) for n in nomes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert resultados == {n: f"Bearer jwt-{n}" for n in nomes}
    a, b = criar_cliente(usuario("a")), criar_cliente(usuario("b"))
    assert a is not b and a.postgrest is not b.postgrest


def test_sem_configuracao_o_erro_e_claro():
    with pytest.raises(ErroAPI) as exc:
        criar_cliente(usuario("ana"))
    assert exc.value.codigo == "supabase_nao_configurado"


# ----------------------------------------------------------- cliente simulado
class Consulta:
    def __init__(self, dono, nome):
        self.dono, self.nome, self.passos = dono, nome, []

    def __getattr__(self, metodo):
        def encadear(*args, **kwargs):
            self.passos.append((metodo, args, kwargs))
            return self
        return encadear

    def execute(self):
        self.dono.chamadas.append((self.nome, self.passos))
        resposta = self.dono.respostas.get(self.nome, [])
        if isinstance(resposta, Exception):
            raise resposta
        return type("R", (), {"data": resposta})()


class Bucket:
    def __init__(self, dono):
        self.dono = dono

    def remove(self, caminhos):
        self.dono.removidos.append(list(caminhos))
        return [{"name": c} for c in caminhos if c not in self.dono.bloqueados]

    def list(self, pasta, opcoes=None):
        desloc = (opcoes or {}).get("offset", 0)
        return self.dono.arquivos.get(pasta, [])[desloc:desloc + 100]

    def exists(self, caminho):
        return caminho in self.dono.bloqueados


class ClienteFalso:
    def __init__(self):
        self.chamadas, self.respostas = [], {}
        self.removidos, self.bloqueados, self.arquivos = [], set(), {}
        self.storage = type("S", (), {"from_": lambda _, nome: Bucket(self)})()

    def table(self, nome):
        return Consulta(self, nome)

    def rpc(self, nome, params):
        c = Consulta(self, f"rpc:{nome}")
        c.passos.append(("params", (params,), {}))
        return c


@pytest.fixture
def repo():
    r = RepositorioSupabase(usuario("ana"), cliente=ClienteFalso())
    return r


def test_recomendacao_e_gravada_em_uma_chamada_atomica(repo):
    """Fase 2 item 5 e fase 3 item 3: eram 1 + 3×2 idas ao banco, sem transação."""
    looks = [{"id": f"l{i}", "posicao": i, "pecas": [{"peca_id": "p", "papel": "superior"}]}
             for i in (1, 2, 3)]
    repo.registrar_recomendacao({"id": "c1", "evento": "casual"}, looks)
    assert len(repo.cliente.chamadas) == 1
    nome, passos = repo.cliente.chamadas[0]
    assert nome == "rpc:registrar_recomendacao"
    assert passos[0][1][0] == {"p_contexto": {"id": "c1", "evento": "casual"}, "p_looks": looks}
    assert "latitude" not in repr(passos)


def test_preferencias_por_categoria_nao_mandam_ids_na_url(repo):
    """Fase 2, item 3: `.in_("look_id", [todos os ids])` estourava a URL."""
    repo.cliente.respostas["rpc:aprovacao_por_categoria"] = [
        {"categoria": "polo", "aprovados": 3, "total": 4}]
    assert repo.aprovacao_por_categoria(200) == {"polo": (3, 4)}
    nome, passos = repo.cliente.chamadas[0]
    assert nome == "rpc:aprovacao_por_categoria" and passos == [("params", ({"p_limite": 200},), {})]


def test_cadastro_nao_calcula_codigo_no_cliente(repo):
    repo.cliente.respostas["pecas"] = [{"id": "1", "codigo": "CLO-000007"}]
    criada = repo.criar_peca({"categoria": "polo"})
    assert criada["codigo"] == "CLO-000007"
    (_, passos), = repo.cliente.chamadas
    enviado = passos[0][1][0]
    assert "codigo" not in enviado and enviado["usuario_id"] == "uid-ana"


def test_remocao_de_foto_e_conferida_e_restrita_a_pasta_do_usuario(repo):
    """O Storage responde 200 com lista vazia quando a RLS barra a remoção; o
    `except: pass` antigo escondia isso."""
    repo.cliente.bloqueados = {"uid-ana/b.webp"}
    removidas = repo.remover_fotos(["uid-ana/a.webp", "uid-ana/b.webp", "uid-outro/c.webp"])
    assert removidas == ["uid-ana/a.webp"]
    assert repo.cliente.removidos == [["uid-ana/a.webp", "uid-ana/b.webp"]]


def test_excluir_conta_apaga_a_pasta_inteira_antes_do_usuario(repo):
    c = repo.cliente
    c.arquivos = {
        "uid-ana": [{"name": f"f{i}.webp", "id": str(i)} for i in range(150)]
                   + [{"name": "sub", "id": None}],
        "uid-ana/sub": [{"name": "g.webp", "id": "x"}],
    }
    c.respostas["pecas"] = [{"id": "1"}, {"id": "2"}]
    resultado = repo.excluir_conta()
    assert resultado == {"pecas_removidas": 2, "fotos_removidas": 151}
    assert sum(len(lote) for lote in c.removidos) == 151
    assert "uid-ana/sub/g.webp" in c.removidos[0]
    assert c.chamadas[-1][0] == "rpc:excluir_minha_conta"


def test_excluir_conta_para_se_alguma_foto_nao_sair(repo):
    c = repo.cliente
    c.arquivos = {"uid-ana": [{"name": "a.webp", "id": "1"}, {"name": "b.webp", "id": "2"}]}
    c.bloqueados = {"uid-ana/b.webp"}
    with pytest.raises(ErroAPI) as exc:
        repo.excluir_conta()
    assert exc.value.codigo == "fotos_nao_removidas"
    assert all(nome != "rpc:excluir_minha_conta" for nome, _ in c.chamadas)


def _api(codigo):
    return APIError({"code": codigo, "message": "m", "details": "d", "hint": "h"})


@pytest.mark.parametrize("falha, status, codigo", [
    (_api("23505"), 409, "registro_duplicado"),
    (_api("PGRST301"), 401, "sessao_expirada"),
    (_api("42501"), 403, "acesso_negado"),
    (_api("PGRST202"), 500, "migracao_pendente"),
    (_api("42703"), 500, "migracao_pendente"),
    (_api("23514"), 422, "dados_invalidos"),
    (_api("XX000"), 502, "banco_falhou"),
    (httpx.ConnectError("sem internet"), 503, "banco_indisponivel"),
    (httpx.ReadTimeout("lento"), 503, "banco_indisponivel"),
])
def test_erros_do_supabase_viram_respostas_adequadas(repo, falha, status, codigo):
    """Fase 2, item 9: tudo virava 500 com stack trace."""
    repo.cliente.respostas["pecas"] = falha
    with pytest.raises(ErroAPI) as exc:
        repo.listar_pecas()
    assert (exc.value.status, exc.value.codigo) == (status, codigo)
    assert "m" != exc.value.mensagem and "Traceback" not in exc.value.mensagem


def test_metricas_e_looks_sao_montados_a_partir_das_linhas(repo):
    repo.cliente.respostas["metricas_recomendacao"] = [{
        "consultas": 3, "consultas_avaliadas": 2, "looks_mostrados": 9,
        "looks_aprovados": 1, "consultas_com_acerto": 1}]
    m = repo.metricas()
    assert m["hit_rate_3"] == 0.5 and m["precision_3"] == round(1 / 6, 4)
    repo.cliente.respostas["metricas_recomendacao"] = []
    assert repo.metricas()["hit_rate_3"] is None

    repo.cliente.respostas["looks"] = [{
        "id": "l1", "posicao": 1, "score": 0.8, "salvo": True,
        "contextos": {"evento": "casual"}, "feedback": [{"aprovado": True}],
        "look_pecas": [{"papel": "superior", "pecas": {"id": "p1"}},
                       {"papel": "calcado", "pecas": None}]}]
    look, = repo.listar_looks(salvos=True, limite=10)
    assert look["aprovado"] is True and look["evento"] == "casual"
    assert look["pecas"] == [{"papel": "superior", "peca": {"id": "p1"}}]
