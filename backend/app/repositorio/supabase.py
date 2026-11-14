"""Repositório sobre o Supabase (produção).

Ponto central de segurança: **um cliente por requisição**, criado com a chave
anônima e com o JWT do usuário no cabeçalho `Authorization`. A versão anterior
chamava `postgrest.auth(token)` num cliente global, o que tinha dois defeitos:

1. requisições simultâneas compartilhavam o cabeçalho — uma podia sair com o
   token de outro usuário (a RLS impede o vazamento, mas a consulta falha ou
   devolve o dado de quem não pediu);
2. `postgrest.auth` autentica só o PostgREST: o Storage continuava anônimo, e
   `storage.remove` não apagava nada (a API responde 200 com lista vazia quando
   a RLS barra a remoção), escondido por um `except: pass`.

Com o token em `ClientOptions(headers=...)`, PostgREST e Storage nascem
autenticados como o usuário, e nada é compartilhado entre requisições.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager

import httpx
from postgrest.exceptions import APIError
from storage3.utils import StorageException
from supabase import Client, ClientOptions, create_client

from ..auth import Usuario
from ..config import config
from ..erros import ErroAPI
from .base import METRICAS_VAZIAS, calcular_metricas

log = logging.getLogger(__name__)

BUCKET = "pecas"
_PAGINA_STORAGE = 100       # limite padrão de `list`
_LOTE_REMOCAO = 1000        # máximo de caminhos por chamada de `remove`

_MIGRACAO_PENDENTE = {"PGRST202", "PGRST204", "PGRST205", "42883", "42P01", "42703"}
_SESSAO = {"PGRST301", "PGRST303"}


def _traduzir_api(exc: APIError, operacao: str) -> ErroAPI:
    codigo = str(getattr(exc, "code", "") or "")
    log.warning("Supabase recusou '%s': [%s] %s", operacao, codigo,
                getattr(exc, "message", exc))
    if codigo in _SESSAO:
        return ErroAPI(401, "sessao_expirada", "Sua sessão expirou. Entre novamente.")
    if codigo == "23505":
        return ErroAPI(409, "registro_duplicado", "Este registro já existe.")
    if codigo == "23503":
        return ErroAPI(409, "referencia_invalida",
                       "O item referenciado não existe mais.")
    if codigo in ("23514", "22P02", "23502"):
        return ErroAPI(422, "dados_invalidos", "Os dados enviados não são válidos.")
    if codigo == "42501":
        return ErroAPI(403, "acesso_negado", "Você não tem acesso a este recurso.")
    if codigo in _MIGRACAO_PENDENTE:
        return ErroAPI(500, "migracao_pendente",
                       "O banco de dados está desatualizado. Aplique as migrações "
                       "de supabase/migrations.")
    return ErroAPI(502, "banco_falhou",
                   "O banco de dados recusou a operação. Tente de novo em instantes.")


@contextmanager
def _protegido(operacao: str):
    """Converte falhas do Supabase em erros da API, sem stack trace para o usuário."""
    try:
        yield
    except ErroAPI:
        raise
    except APIError as exc:
        raise _traduzir_api(exc, operacao) from exc
    except StorageException as exc:
        log.warning("Storage falhou em '%s': %s", operacao, exc)
        raise ErroAPI(502, "armazenamento_falhou",
                      "Não foi possível acessar o armazenamento de fotos.") from exc
    except httpx.TimeoutException as exc:
        raise ErroAPI(503, "banco_indisponivel",
                      "O banco de dados demorou a responder. Tente de novo.") from exc
    except httpx.HTTPError as exc:
        log.warning("Rede falhou em '%s': %s", operacao, exc)
        raise ErroAPI(503, "banco_indisponivel",
                      "Sem conexão com o banco de dados. Verifique a internet "
                      "e tente de novo.") from exc


def criar_cliente(usuario: Usuario) -> Client:
    if not config.configurado:
        raise ErroAPI(503, "supabase_nao_configurado",
                      "Supabase não configurado. Defina SUPABASE_URL e "
                      "SUPABASE_ANON_KEY no arquivo .env.")
    return create_client(
        config.supabase_url, config.supabase_anon_key,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {usuario.token}"},
            auto_refresh_token=False, persist_session=False,
        ),
    )


class RepositorioSupabase:
    def __init__(self, usuario: Usuario, cliente: Client | None = None):
        self.usuario = usuario
        self.uid = usuario.id
        self.cliente = cliente or criar_cliente(usuario)

    def fechar(self) -> None:
        """Libera as conexões HTTP abertas por esta requisição."""
        for nome in ("_postgrest", "_storage"):
            alvo = getattr(self.cliente, nome, None)
            sessao = getattr(alvo, "session", None) or getattr(alvo, "_client", None)
            try:
                if sessao is not None:
                    sessao.close()
            except Exception:                    # noqa: BLE001 — só limpeza
                pass

    def _tabela(self, nome: str):
        return self.cliente.table(nome)

    # ------------------------------------------------------------- peças
    def listar_pecas(self, *, papel=None, categoria=None, cor=None, disponivel=None):
        with _protegido("listar peças"):
            consulta = self._tabela("pecas").select("*")
            if papel:
                consulta = consulta.eq("papel", papel)
            if categoria:
                consulta = consulta.eq("categoria", categoria)
            if cor:
                consulta = consulta.eq("cor_nome", cor)
            if disponivel is not None:
                consulta = consulta.eq("disponivel", disponivel)
            return consulta.order("criado_em", desc=True).execute().data or []

    def obter_peca(self, peca_id):
        with _protegido("ler peça"):
            linhas = self._tabela("pecas").select("*").eq("id", peca_id).execute().data
            return linhas[0] if linhas else None

    def criar_peca(self, dados):
        # o código CLO é atribuído por gatilho no banco (contador por usuário):
        # uma ida só, sem corrida entre "ler o próximo" e "inserir"
        linha = {**dados, "usuario_id": self.uid, "revisada": True}
        with _protegido("registrar peça"):
            return self._tabela("pecas").insert(linha).execute().data[0]

    def atualizar_peca(self, peca_id, campos):
        with _protegido("atualizar peça"):
            linhas = (self._tabela("pecas").update(campos)
                      .eq("id", peca_id).execute().data)
            return linhas[0] if linhas else None

    def remover_peca(self, peca_id):
        with _protegido("remover peça"):
            linhas = self._tabela("pecas").delete().eq("id", peca_id).execute().data
            return linhas[0] if linhas else None

    def remover_fotos(self, caminhos):
        """Apaga arquivos do bucket e devolve os que de fato sumiram.

        O Storage responde 200 mesmo quando a RLS impede a remoção — a prova de
        que apagou é o item aparecer na resposta. Por isso o retorno é conferido
        pelo chamador, em vez de presumido.
        """
        # só a pasta do próprio usuário; a política do bucket garante o mesmo
        proprios = [c for c in caminhos if c and c.startswith(self.uid + "/")]
        removidos: list[str] = []
        with _protegido("remover fotos"):
            bucket = self.cliente.storage.from_(BUCKET)
            for i in range(0, len(proprios), _LOTE_REMOCAO):
                resposta = bucket.remove(proprios[i:i + _LOTE_REMOCAO]) or []
                removidos += [o.get("name") for o in resposta if isinstance(o, dict)]
        return [c for c in removidos if c]

    def foto_existe(self, caminho):
        with _protegido("conferir foto"):
            return bool(self.cliente.storage.from_(BUCKET).exists(caminho))

    def _listar_pasta(self, pasta: str) -> list[str]:
        """Todos os arquivos sob `pasta`, descendo em subpastas."""
        bucket = self.cliente.storage.from_(BUCKET)
        arquivos: list[str] = []
        deslocamento = 0
        while True:
            pagina = bucket.list(pasta, {"limit": _PAGINA_STORAGE, "offset": deslocamento}) or []
            for item in pagina:
                caminho = f"{pasta}/{item['name']}"
                if item.get("id") is None:           # pasta: o Storage não lhe dá id
                    arquivos += self._listar_pasta(caminho)
                else:
                    arquivos.append(caminho)
            if len(pagina) < _PAGINA_STORAGE:
                return arquivos
            deslocamento += _PAGINA_STORAGE

    # ------------------------------------------------------ recomendação
    def usos_recentes(self, janela):
        with _protegido("ler histórico de looks"):
            linhas = self.cliente.rpc("usos_recentes", {"p_janela": janela}).execute().data
            return {l["peca_id"]: l["usos"] for l in linhas or []}

    def aprovacao_por_categoria(self, limite):
        # agregado no banco: a versão anterior mandava todos os IDs de look na
        # URL (`in.(...)`), que estoura o limite de ~16 KB com o histórico crescendo
        with _protegido("ler preferências por categoria"):
            linhas = self.cliente.rpc("aprovacao_por_categoria",
                                      {"p_limite": limite}).execute().data
            return {l["categoria"]: (l["aprovados"], l["total"]) for l in linhas or []}

    def pesos(self):
        with _protegido("ler pesos"):
            linhas = (self._tabela("preferencias").select("pesos")
                      .eq("usuario_id", self.uid).execute().data)
            return linhas[0]["pesos"] if linhas else None

    def salvar_pesos(self, pesos):
        with _protegido("salvar pesos"):
            self._tabela("preferencias").upsert(
                {"usuario_id": self.uid, "pesos": pesos},
                on_conflict="usuario_id").execute()

    def registrar_recomendacao(self, contexto, looks):
        # uma chamada, uma transação: contexto, looks e peças dos looks entram
        # juntos ou não entra nada — não sobra contexto órfão para sujar as métricas
        with _protegido("registrar recomendação"):
            self.cliente.rpc("registrar_recomendacao",
                             {"p_contexto": contexto, "p_looks": looks}).execute()

    def obter_look(self, look_id):
        with _protegido("ler look"):
            linhas = self._tabela("looks").select("*").eq("id", look_id).execute().data
            return linhas[0] if linhas else None

    def registrar_feedback(self, look_id, aprovado):
        with _protegido("registrar feedback"):
            self._tabela("feedback").upsert(
                {"usuario_id": self.uid, "look_id": look_id, "aprovado": aprovado},
                on_conflict="usuario_id,look_id").execute()

    def marcar_look_salvo(self, look_id, salvo):
        with _protegido("salvar look"):
            linhas = (self._tabela("looks").update({"salvo": salvo})
                      .eq("id", look_id).execute().data)
            return bool(linhas)

    def listar_looks(self, *, salvos, limite):
        with _protegido("listar looks"):
            consulta = self._tabela("looks").select(
                "*, contextos(evento), feedback(aprovado), look_pecas(papel, pecas(*))")
            if salvos:
                consulta = consulta.eq("salvo", True)
            linhas = consulta.order("criado_em", desc=True).limit(limite).execute().data or []
        saida = []
        for l in linhas:
            votos = l.pop("feedback", None) or []
            contexto = l.pop("contextos", None) or {}
            vinculos = l.pop("look_pecas", None) or []
            saida.append({
                **l,
                "aprovado": votos[0]["aprovado"] if votos else None,
                "evento": contexto.get("evento"),
                "pecas": [{"papel": v["papel"], "peca": v["pecas"]}
                          for v in vinculos if v.get("pecas")],
            })
        return saida

    def metricas(self):
        with _protegido("ler métricas"):
            linhas = self._tabela("metricas_recomendacao").select("*").execute().data
        if not linhas:
            return dict(METRICAS_VAZIAS)
        m = linhas[0]
        return calcular_metricas(m["consultas"], m["consultas_avaliadas"],
                                 m["looks_mostrados"], m["looks_aprovados"],
                                 m["consultas_com_acerto"])

    # ----------------------------------------------------- perfil e LGPD
    def perfil(self):
        with _protegido("ler perfil"):
            linhas = self._tabela("perfis").select("*").eq("id", self.uid).execute().data
        base = linhas[0] if linhas else {"id": self.uid, "nome": None, "criado_em": None}
        return {**base, "email": self.usuario.email}

    def atualizar_perfil(self, nome):
        with _protegido("atualizar perfil"):
            self._tabela("perfis").upsert({"id": self.uid, "nome": nome},
                                          on_conflict="id").execute()
        return self.perfil()

    def consentimento(self):
        with _protegido("ler consentimento"):
            linhas = (self._tabela("consentimentos").select("*")
                      .eq("usuario_id", self.uid)
                      .order("aceito_em", desc=True).limit(1).execute().data)
            return linhas[0] if linhas else None

    def registrar_consentimento(self, versao, finalidades):
        with _protegido("registrar consentimento"):
            return self._tabela("consentimentos").insert({
                "usuario_id": self.uid, "versao": versao, "finalidades": finalidades,
            }).execute().data[0]

    def revogar_consentimento(self):
        with _protegido("revogar consentimento"):
            self.cliente.rpc("revogar_consentimento", {}).execute()

    def exportar_dados(self):
        with _protegido("exportar dados"):
            ler = lambda tabela: self._tabela(tabela).select("*").execute().data or []  # noqa: E731
            return {
                "perfil": self.perfil(),
                "consentimentos": ler("consentimentos"),
                "pecas": ler("pecas"),
                "contextos": ler("contextos"),
                "looks": self._tabela("looks").select("*, look_pecas(peca_id, papel)")
                             .execute().data or [],
                "feedback": ler("feedback"),
                "preferencias": (ler("preferencias") or [None])[0],
            }

    def excluir_conta(self):
        """Apaga as fotos do usuário e, depois, a conta com tudo o que depende dela.

        A ordem importa. Os arquivos só saem pela API do Storage (o banco bloqueia
        `delete` direto em `storage.objects`), e precisam do token do usuário —
        que deixa de valer para novas sessões quando a conta some. Só depois de
        confirmar a pasta vazia a função `excluir_minha_conta` remove o usuário
        de `auth.users`, e o `on delete cascade` leva perfil, peças, contextos,
        looks, feedback, preferências e consentimentos.
        """
        with _protegido("excluir conta"):
            arquivos = self._listar_pasta(self.uid)
        removidos = self.remover_fotos(arquivos) if arquivos else []
        if len(removidos) < len(arquivos):
            log.error("Exclusão de conta interrompida: %d de %d fotos removidas",
                      len(removidos), len(arquivos))
            raise ErroAPI(502, "fotos_nao_removidas",
                          "Não foi possível apagar todas as suas fotos. Nada foi "
                          "excluído da conta; tente de novo em instantes.")
        with _protegido("excluir conta"):
            pecas = len(self._tabela("pecas").select("id").execute().data or [])
            self.cliente.rpc("excluir_minha_conta", {}).execute()
        return {"pecas_removidas": pecas, "fotos_removidas": len(removidos)}
