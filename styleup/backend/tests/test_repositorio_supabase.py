"""Testes da implementação Supabase do repositório.

Antes desta suíte, `RepositorioSupabase` nunca havia executado: os testes de API
rodam em modo demonstração, e o código de produção só era exercitado pelo
usuário final. Um nome de coluna errado ou um filtro invertido só apareceria
depois do deploy.

O duplo abaixo imita a API fluente do supabase-py e registra a consulta montada,
o que permite afirmar *o que* foi pedido ao banco, não só que nada explodiu.
"""

from __future__ import annotations

import pytest

from app.repositorio import JANELA_PREFERENCIA, JANELA_VARIEDADE, RepositorioSupabase


class ConsultaFalsa:
    """Encadeia como o postgrest-py e guarda o que foi montado."""

    def __init__(self, tabela: str, registro: dict, dados):
        self.tabela = tabela
        self.registro = registro
        self._dados = dados
        registro.setdefault("filtros", [])
        registro.setdefault("ordem", [])

    def select(self, *colunas):
        self.registro["select"] = colunas
        return self

    def insert(self, valores):
        self.registro["insert"] = valores
        self._dados = valores if isinstance(valores, list) else [valores]
        # o banco devolve as linhas com id; simulamos isso
        self._dados = [{**linha, "id": f"id-{i}"} for i, linha in enumerate(self._dados)]
        return self

    def update(self, valores):
        self.registro["update"] = valores
        return self

    def upsert(self, valores, on_conflict=None):
        self.registro["upsert"] = valores
        self.registro["on_conflict"] = on_conflict
        return self

    def delete(self):
        self.registro["delete"] = True
        return self

    def eq(self, campo, valor):
        self.registro["filtros"].append(("eq", campo, valor))
        return self

    def in_(self, campo, valores):
        self.registro["filtros"].append(("in", campo, list(valores)))
        return self

    def order(self, campo, desc=False):
        self.registro["ordem"].append((campo, desc))
        return self

    def limit(self, n):
        self.registro["limite"] = n
        return self

    def execute(self):
        return type("Resposta", (), {"data": self._dados})()


class ClienteFalso:
    def __init__(self, dados_por_tabela: dict | None = None, rpc=None):
        self.dados = dados_por_tabela or {}
        self.consultas: list[dict] = []
        self._rpc = rpc
        self.storage_removidos: list[str] = []

        cliente = self

        class Bucket:
            def remove(self, caminhos):
                cliente.storage_removidos.extend(caminhos)

        class Storage:
            def from_(self, _nome):
                return Bucket()

        self.storage = Storage()

    def table(self, nome):
        registro = {"tabela": nome}
        self.consultas.append(registro)
        return ConsultaFalsa(nome, registro, list(self.dados.get(nome, [])))

    def rpc(self, nome, params):
        self.consultas.append({"rpc": nome, "params": params})
        return type("R", (), {"execute": lambda _s: type(
            "Resp", (), {"data": self._rpc})()})()

    def consulta(self, tabela: str) -> dict:
        return next(c for c in self.consultas if c.get("tabela") == tabela)


def repo(cliente, usuario="ana"):
    return RepositorioSupabase(cliente, usuario)


# ------------------------------------------------------------------- peças
def test_listar_pecas_filtra_e_ordena():
    cliente = ClienteFalso({"pecas": [{"id": "1", "categoria": "camiseta"}]})
    resultado = repo(cliente).listar_pecas(papel="superior", disponivel=True,
                                           categoria=None)

    consulta = cliente.consulta("pecas")
    assert ("eq", "papel", "superior") in consulta["filtros"]
    assert ("eq", "disponivel", True) in consulta["filtros"]
    # filtro None não deve virar cláusula: viraria "categoria is null"
    assert all(f[1] != "categoria" for f in consulta["filtros"])
    assert consulta["ordem"] == [("criado_em", True)]
    # o rótulo é acrescentado a partir da taxonomia
    assert resultado[0]["rotulo"] == "Camiseta"


def test_criar_peca_injeta_usuario_e_codigo():
    cliente = ClienteFalso({"pecas": []}, rpc="CLO-000007")
    criada = repo(cliente).criar_peca({"categoria": "polo", "papel": "superior"})

    inserido = cliente.consulta("pecas")["insert"]
    assert inserido["usuario_id"] == "ana"
    assert inserido["codigo"] == "CLO-000007"
    assert inserido["revisada"] is True
    assert criada["rotulo"] == "Camisa polo"


def test_atualizar_peca_inexistente_devolve_none():
    cliente = ClienteFalso({"pecas": []})
    assert repo(cliente).atualizar_peca("id-x", {"disponivel": False}) is None


def test_remover_peca_apaga_a_imagem_do_bucket():
    """RNF11 fala em remoção efetiva, não só do registro."""
    cliente = ClienteFalso({"pecas": [{"imagem_path": "ana/foto.jpg"}]})
    caminho = repo(cliente).remover_peca("id-1")

    assert caminho == "ana/foto.jpg"
    assert cliente.storage_removidos == ["ana/foto.jpg"]


def test_remover_peca_sem_imagem_nao_chama_o_storage():
    cliente = ClienteFalso({"pecas": [{"imagem_path": None}]})
    assert repo(cliente).remover_peca("id-1") == ""
    assert cliente.storage_removidos == []


# ------------------------------------------------------------------ looks
def test_salvar_looks_usa_dois_inserts_em_lote():
    """Um insert por look e outro por vínculo eram seis idas ao banco."""
    cliente = ClienteFalso()
    looks = [
        {"posicao": 1, "score": 0.9, "parcelas": {}, "explicacao": "a",
         "pecas": {"superior": "p1", "inferior": "p2", "calcado": "p3"}},
        {"posicao": 2, "score": 0.8, "parcelas": {}, "explicacao": "b",
         "pecas": {"superior": "p1", "inferior": "p4", "calcado": "p3"}},
    ]
    repo(cliente).salvar_looks("ctx-1", looks)

    inserts = [c for c in cliente.consultas if "insert" in c]
    assert len(inserts) == 2                       # looks + look_pecas

    registros_looks = cliente.consulta("looks")["insert"]
    assert len(registros_looks) == 2
    assert all(r["contexto_id"] == "ctx-1" for r in registros_looks)
    assert all(r["usuario_id"] == "ana" for r in registros_looks)

    vinculos = cliente.consulta("look_pecas")["insert"]
    assert len(vinculos) == 6                      # 2 looks × 3 peças
    assert {v["papel"] for v in vinculos} == {"superior", "inferior", "calcado"}


def test_usos_recentes_limita_a_janela():
    cliente = ClienteFalso({
        "looks": [{"id": f"l{i}"} for i in range(20)],
        "look_pecas": [{"peca_id": "p1"}, {"peca_id": "p1"}, {"peca_id": "p2"}],
    })
    contagem = repo(cliente).usos_recentes()

    assert cliente.consulta("looks")["limite"] == JANELA_VARIEDADE
    assert contagem == {"p1": 2, "p2": 1}


def test_usos_recentes_sem_looks_nao_consulta_vinculos():
    cliente = ClienteFalso({"looks": []})
    assert repo(cliente).usos_recentes() == {}
    assert all(c.get("tabela") != "look_pecas" for c in cliente.consultas)


# -------------------------------------------------------------- preferência
def test_taxa_por_categoria_limita_o_historico():
    """Ler todo o histórico crescia sem limite dentro do orçamento do RNF02."""
    cliente = ClienteFalso({
        "feedback": [{"look_id": "l1", "aprovado": True},
                     {"look_id": "l2", "aprovado": False}],
        "look_pecas": [
            {"look_id": "l1", "pecas": {"categoria": "polo"}},
            {"look_id": "l2", "pecas": {"categoria": "polo"}},
            {"look_id": "l1", "pecas": {"categoria": "tenis"}},
        ],
    })
    taxas = repo(cliente).taxa_por_categoria()

    assert cliente.consulta("feedback")["limite"] == JANELA_PREFERENCIA
    assert taxas == {"polo": 0.5, "tenis": 1.0}


def test_taxa_por_categoria_sem_feedback_devolve_vazio():
    cliente = ClienteFalso({"feedback": []})
    assert repo(cliente).taxa_por_categoria() == {}


def test_pesos_ausentes_devolvem_none():
    """Quem nunca deu feedback usa os pesos padrão, decidido na rota."""
    cliente = ClienteFalso({"preferencias": []})
    assert repo(cliente).obter_pesos() is None


def test_salvar_pesos_usa_upsert_por_usuario():
    cliente = ClienteFalso()
    repo(cliente).salvar_pesos({"cor": 0.5})
    consulta = cliente.consulta("preferencias")
    assert consulta["upsert"]["usuario_id"] == "ana"
    assert consulta["on_conflict"] == "usuario_id"


def test_feedback_usa_upsert_para_nao_duplicar():
    cliente = ClienteFalso()
    repo(cliente).registrar_feedback("look-1", True)
    consulta = cliente.consulta("feedback")
    assert consulta["on_conflict"] == "usuario_id,look_id"
    assert consulta["upsert"]["aprovado"] is True


def test_metricas_vazias_tem_a_mesma_forma_do_modo_memoria():
    """Os dois repositórios têm de responder com as mesmas chaves."""
    from app.repositorio import RepositorioMemoria, limpar_armazens

    limpar_armazens()
    cliente = ClienteFalso({"metricas_recomendacao": []})
    try:
        assert set(repo(cliente).metricas()) == set(
            RepositorioMemoria("ana").metricas())
    finally:
        limpar_armazens()


@pytest.mark.parametrize("metodo, argumentos", [
    ("listar_pecas", {}),
    ("usos_recentes", {}),
    ("taxa_por_categoria", {}),
])
def test_tabela_vazia_nunca_gera_excecao(metodo, argumentos):
    """O supabase-py pode devolver `data=None`; nada disso pode virar 500."""
    cliente = ClienteFalso({})
    resultado = getattr(repo(cliente), metodo)(**argumentos)
    assert resultado in ([], {}) or isinstance(resultado, (list, dict))
