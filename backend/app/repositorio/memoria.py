"""Repositório em memória: modo demonstração e testes.

Replica as regras que, em produção, são do banco: isolamento por usuário (o que
a RLS faz), código CLO por contador, exclusão em cascata. Os dados somem quando
o processo reinicia — é uma vitrine, não um banco.
"""

from __future__ import annotations

import threading
import uuid
from collections import Counter
from datetime import datetime, timezone

from ..auth import Usuario
from ..services.cor import HEX_REFERENCIA, hex_para_hsv, nomear
from ..services.taxonomia import POR_CHAVE
from .base import calcular_metricas

_trava = threading.RLock()


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class Armazem:
    """Tudo o que o modo demonstração guarda. Um por processo."""

    def __init__(self) -> None:
        self.limpar()

    def limpar(self) -> None:
        self.pecas: dict[str, dict] = {}
        self.contextos: dict[str, dict] = {}
        self.looks: dict[str, dict] = {}
        self.feedback: dict[tuple[str, str], dict] = {}
        self.preferencias: dict[str, dict] = {}
        self.perfis: dict[str, dict] = {}
        self.consentimentos: list[dict] = []
        self.contadores: Counter = Counter()
        self.fotos: dict[str, tuple[bytes, str]] = {}
        self.semeados: set[str] = set()
        self.falhar_ao_gravar_looks = False      # só para testes do contexto órfão


armazem = Armazem()

# Guarda-roupa de exemplo do visitante do modo demonstração: pequeno, mas cobre
# calor, frio, trabalho e treino, para todas as inspirações darem resultado.
_SEMENTE: tuple[tuple[str, str, dict], ...] = (
    ("camiseta", "preto", {"estampa": "lisa", "manga": "curta"}),
    ("camiseta", "branco", {"estampa": "lisa", "manga": "curta"}),
    ("camiseta", "verde-oliva", {"estampa": "lisa", "manga": "curta"}),
    ("polo", "marinho", {"estampa": "lisa", "manga": "curta"}),
    ("camisa-casual", "azul-claro", {"estampa": "lisa", "manga": "longa"}),
    ("camisa-social", "branco", {"estampa": "lisa", "manga": "longa"}),
    ("moletom", "cinza", {"estampa": "lisa", "manga": "longa"}),
    ("moletom", "vinho", {"estampa": "lisa", "manga": "longa"}),
    ("bermuda", "bege", {"estampa": "lisa"}),
    ("calca-jeans", "azul", {"estampa": "lisa"}),
    ("calca-sarja", "cáqui", {"estampa": "lisa"}),
    ("calca-social", "grafite", {"estampa": "lisa"}),
    ("calca-moletom", "grafite", {"estampa": "lisa"}),
    ("tenis", "preto", {}),
    ("tenis-casual", "branco", {}),
    ("bota", "marrom", {}),
    ("sapato-social", "preto", {}),
    ("chinelo", "preto", {}),
    ("jaqueta-jeans", "azul", {"estampa": "lisa"}),
    ("corta-vento", "verde-oliva", {"estampa": "lisa"}),
    ("blazer", "marinho", {"estampa": "lisa"}),
    ("bone", "grafite", {}),
    ("cinto", "preto", {}),
    ("relogio", "preto", {}),
)


def peca_de_exemplo(categoria: str, cor_nome: str, atributos: dict | None = None) -> dict:
    """Linha de peça pronta para `criar_peca`, a partir da taxonomia e do nome da cor."""
    cat = POR_CHAVE[categoria]
    cor_hex = HEX_REFERENCIA[cor_nome]
    h, s, v = hex_para_hsv(cor_hex)
    return {
        "categoria": categoria, "papel": cat.papel, "formalidade": cat.formalidade,
        "cor_nome": cor_nome, "cor_hex": cor_hex,
        "cor_hsv": [round(h, 2), round(s, 4), round(v, 4)],
        "neutra": nomear(h, s, v)[1],
        "temp_min": cat.temp_min, "temp_max": cat.temp_max,
        "resiste_chuva": cat.resiste_chuva, "atributos": dict(atributos or {}),
        "imagem_path": None, "confianca": {},
    }


class RepositorioMemoria:
    def __init__(self, usuario: Usuario, dados: Armazem | None = None,
                 semear: bool = False):
        self.usuario = usuario
        self.uid = usuario.id
        self.dados = dados or armazem
        with _trava:
            if self.uid not in self.dados.perfis:
                nome = (usuario.email or "visitante").split("@")[0].capitalize()
                self.dados.perfis[self.uid] = {"id": self.uid, "nome": nome,
                                               "criado_em": _agora()}
            if semear and self.uid not in self.dados.semeados:
                self.dados.semeados.add(self.uid)
                for categoria, cor, atributos in _SEMENTE:
                    self.criar_peca(peca_de_exemplo(categoria, cor, atributos))

    # ------------------------------------------------------------- peças
    def _minhas(self) -> list[dict]:
        return [p for p in self.dados.pecas.values() if p["usuario_id"] == self.uid]

    def listar_pecas(self, *, papel=None, categoria=None, cor=None, disponivel=None):
        with _trava:
            linhas = self._minhas()
            if papel:
                linhas = [p for p in linhas if p["papel"] == papel]
            if categoria:
                linhas = [p for p in linhas if p["categoria"] == categoria]
            if cor:
                linhas = [p for p in linhas if p["cor_nome"] == cor]
            if disponivel is not None:
                linhas = [p for p in linhas if p["disponivel"] is disponivel]
            return [dict(p) for p in sorted(linhas, key=lambda p: p["_ordem"], reverse=True)]

    def obter_peca(self, peca_id):
        with _trava:
            p = self.dados.pecas.get(peca_id)
            return dict(p) if p and p["usuario_id"] == self.uid else None

    def criar_peca(self, dados):
        with _trava:
            # contador por usuário: nunca reaproveita número, mesmo após exclusão
            self.dados.contadores[self.uid] += 1
            numero = self.dados.contadores[self.uid]
            linha = {
                **dados, "id": str(uuid.uuid4()), "usuario_id": self.uid,
                "codigo": f"CLO-{numero:06d}", "disponivel": True, "revisada": True,
                "criado_em": _agora(), "_ordem": numero,
            }
            self.dados.pecas[linha["id"]] = linha
            return dict(linha)

    def atualizar_peca(self, peca_id, campos):
        with _trava:
            p = self.dados.pecas.get(peca_id)
            if not p or p["usuario_id"] != self.uid:
                return None
            p.update(campos)
            return dict(p)

    def remover_peca(self, peca_id):
        with _trava:
            p = self.dados.pecas.get(peca_id)
            if not p or p["usuario_id"] != self.uid:
                return None
            del self.dados.pecas[peca_id]
            # cascata de look_pecas: o look perde a peça, como no banco
            for look in self.dados.looks.values():
                look["pecas"] = [v for v in look["pecas"] if v["peca_id"] != peca_id]
            return dict(p)

    def remover_fotos(self, caminhos):
        with _trava:
            removidas = []
            for caminho in caminhos:
                if caminho.startswith(self.uid + "/") and self.dados.fotos.pop(caminho, None):
                    removidas.append(caminho)
            return removidas

    def foto_existe(self, caminho):
        with _trava:
            return caminho in self.dados.fotos

    # fotos do modo demonstração (em produção o navegador fala direto com o Storage)
    def salvar_foto(self, conteudo: bytes, tipo: str) -> str:
        extensao = {"image/webp": "webp", "image/png": "png"}.get(tipo, "jpg")
        caminho = f"{self.uid}/{uuid.uuid4()}.{extensao}"
        with _trava:
            self.dados.fotos[caminho] = (conteudo, tipo)
        return caminho

    # ------------------------------------------------------ recomendação
    def _meus_looks(self) -> list[dict]:
        return sorted((l for l in self.dados.looks.values() if l["usuario_id"] == self.uid),
                      key=lambda l: l["_ordem"], reverse=True)

    def usos_recentes(self, janela):
        with _trava:
            contagem: Counter = Counter()
            for look in self._meus_looks()[:janela]:
                contagem.update(v["peca_id"] for v in look["pecas"])
            return dict(contagem)

    def aprovacao_por_categoria(self, limite):
        with _trava:
            meus = sorted((f for f in self.dados.feedback.values()
                           if f["usuario_id"] == self.uid),
                          key=lambda f: f["_ordem"], reverse=True)[:limite]
            resultado: dict[str, list[int]] = {}
            for f in meus:
                look = self.dados.looks.get(f["look_id"])
                for vinculo in (look or {}).get("pecas", []):
                    peca = self.dados.pecas.get(vinculo["peca_id"])
                    if peca:
                        par = resultado.setdefault(peca["categoria"], [0, 0])
                        par[0] += 1 if f["aprovado"] else 0
                        par[1] += 1
            return {c: (a, t) for c, (a, t) in resultado.items()}

    def pesos(self):
        with _trava:
            linha = self.dados.preferencias.get(self.uid)
            return dict(linha["pesos"]) if linha else None

    def salvar_pesos(self, pesos):
        with _trava:
            self.dados.preferencias[self.uid] = {"pesos": dict(pesos), "atualizado": _agora()}

    def registrar_recomendacao(self, contexto, looks):
        with _trava:
            # tudo ou nada, como a função SQL: se os looks falharem, o contexto não fica
            if self.dados.falhar_ao_gravar_looks:
                raise RuntimeError("falha simulada ao gravar looks")
            ordem = len(self.dados.contextos) + 1
            self.dados.contextos[contexto["id"]] = {
                **contexto, "usuario_id": self.uid, "criado_em": _agora(), "_ordem": ordem}
            for look in looks:
                self.dados.looks[look["id"]] = {
                    **look, "pecas": [dict(v) for v in look["pecas"]],
                    "usuario_id": self.uid, "contexto_id": contexto["id"],
                    "salvo": False, "criado_em": _agora(),
                    "_ordem": len(self.dados.looks) + 1,
                }

    def obter_look(self, look_id):
        with _trava:
            look = self.dados.looks.get(look_id)
            return dict(look) if look and look["usuario_id"] == self.uid else None

    def registrar_feedback(self, look_id, aprovado):
        with _trava:
            anterior = self.dados.feedback.get((self.uid, look_id))
            self.dados.feedback[(self.uid, look_id)] = {
                "usuario_id": self.uid, "look_id": look_id, "aprovado": aprovado,
                "criado_em": _agora(),
                "_ordem": anterior["_ordem"] if anterior else len(self.dados.feedback) + 1,
            }

    def marcar_look_salvo(self, look_id, salvo):
        with _trava:
            look = self.dados.looks.get(look_id)
            if not look or look["usuario_id"] != self.uid:
                return False
            look["salvo"] = salvo
            return True

    def listar_looks(self, *, salvos, limite):
        with _trava:
            saida = []
            for look in self._meus_looks():
                if salvos and not look["salvo"]:
                    continue
                voto = self.dados.feedback.get((self.uid, look["id"]))
                contexto = self.dados.contextos.get(look["contexto_id"], {})
                saida.append({
                    **{k: v for k, v in look.items() if not k.startswith("_")},
                    "aprovado": voto["aprovado"] if voto else None,
                    "evento": contexto.get("evento"),
                    "pecas": [{"papel": v["papel"], "peca": dict(self.dados.pecas[v["peca_id"]])}
                              for v in look["pecas"] if v["peca_id"] in self.dados.pecas],
                })
                if len(saida) >= limite:
                    break
            return saida

    def metricas(self):
        with _trava:
            contextos = [c for c in self.dados.contextos.values()
                         if c["usuario_id"] == self.uid]
            mostrados = aprovados = avaliadas = com_acerto = 0
            for c in contextos:
                looks = [l for l in self.dados.looks.values() if l["contexto_id"] == c["id"]]
                votos = [self.dados.feedback.get((self.uid, l["id"])) for l in looks]
                votos = [v for v in votos if v]
                mostrados += len(looks)
                positivos = sum(1 for v in votos if v["aprovado"])
                aprovados += positivos
                avaliadas += 1 if votos else 0
                com_acerto += 1 if positivos else 0
            return calcular_metricas(len(contextos), avaliadas, mostrados,
                                     aprovados, com_acerto)

    # ----------------------------------------------------- perfil e LGPD
    def perfil(self):
        with _trava:
            return {**self.dados.perfis[self.uid], "email": self.usuario.email}

    def atualizar_perfil(self, nome):
        with _trava:
            self.dados.perfis[self.uid]["nome"] = nome
            return self.perfil()

    def consentimento(self):
        with _trava:
            meus = [c for c in self.dados.consentimentos if c["usuario_id"] == self.uid]
            return dict(meus[-1]) if meus else None

    def registrar_consentimento(self, versao, finalidades):
        with _trava:
            linha = {"id": str(uuid.uuid4()), "usuario_id": self.uid, "versao": versao,
                     "finalidades": dict(finalidades), "aceito_em": _agora(),
                     "revogado_em": None}
            self.dados.consentimentos.append(linha)
            return dict(linha)

    def revogar_consentimento(self):
        with _trava:
            for c in self.dados.consentimentos:
                if c["usuario_id"] == self.uid and c["revogado_em"] is None:
                    c["revogado_em"] = _agora()

    def exportar_dados(self):
        with _trava:
            limpar = lambda d: {k: v for k, v in d.items() if not k.startswith("_")}  # noqa: E731
            return {
                "perfil": self.perfil(),
                "consentimentos": [dict(c) for c in self.dados.consentimentos
                                   if c["usuario_id"] == self.uid],
                "pecas": [limpar(p) for p in self._minhas()],
                "contextos": [limpar(c) for c in self.dados.contextos.values()
                              if c["usuario_id"] == self.uid],
                "looks": [limpar(l) for l in self._meus_looks()],
                "feedback": [limpar(f) for f in self.dados.feedback.values()
                             if f["usuario_id"] == self.uid],
                "preferencias": self.dados.preferencias.get(self.uid),
            }

    def excluir_conta(self):
        with _trava:
            d = self.dados
            fotos = [c for c in d.fotos if c.startswith(self.uid + "/")]
            for caminho in fotos:
                del d.fotos[caminho]
            pecas = [k for k, p in d.pecas.items() if p["usuario_id"] == self.uid]
            for k in pecas:
                del d.pecas[k]
            for tabela in (d.contextos, d.looks):
                for k in [k for k, v in tabela.items() if v["usuario_id"] == self.uid]:
                    del tabela[k]
            for k in [k for k in d.feedback if k[0] == self.uid]:
                del d.feedback[k]
            d.consentimentos = [c for c in d.consentimentos if c["usuario_id"] != self.uid]
            d.preferencias.pop(self.uid, None)
            d.perfis.pop(self.uid, None)
            d.contadores.pop(self.uid, None)
            d.semeados.discard(self.uid)
            return {"pecas_removidas": len(pecas), "fotos_removidas": len(fotos)}
