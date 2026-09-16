"""Camada de persistência do StyleUp.

Por que existe: as rotas antes falavam direto com o Supabase, o que tornava
impossível rodar ou testar o fluxo sem um projeto na nuvem já configurado. Com
esta abstração há duas implementações:

* `RepositorioSupabase` — produção. Usa a chave anônima e o JWT do usuário, de
  modo que as políticas de RLS continuam valendo dentro da API.
* `RepositorioMemoria` — modo demonstração. Guarda tudo no processo e já vem
  semeado com um guarda-roupa de exemplo, então `uvicorn` + `npm run dev`
  entregam o fluxo completo sem nenhuma credencial.

Todo repositório é criado **por usuário**: não existe método que receba
`usuario_id`, e portanto não existe caminho de código capaz de ler os dados de
outra pessoa por descuido.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from .services.taxonomia import POR_CHAVE

JANELA_VARIEDADE = 10          # quantos looks recentes contam para a penalização

# Quantos feedbacks entram no cálculo da preferência por categoria.
#
# A versão anterior lia *todo* o histórico de feedback do usuário e, em seguida,
# todos os vínculos daqueles looks. O custo crescia sem limite com o uso, dentro
# do orçamento de 3 s do RNF02. Cem avaliações recentes descrevem o gosto atual
# melhor que o histórico completo — preferência muda, e o registro antigo pesa
# contra a personalização.
JANELA_PREFERENCIA = 100


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repositorio(Protocol):
    """Contrato que as rotas usam. Implementações não vazam detalhe de storage."""

    # ------------------------------------------------------------------ peças
    def proximo_codigo(self) -> str: ...
    def listar_pecas(self, **filtros: Any) -> list[dict]: ...
    def criar_peca(self, dados: dict) -> dict: ...
    def atualizar_peca(self, peca_id: str, campos: dict) -> dict | None: ...
    def remover_peca(self, peca_id: str) -> str | None: ...

    # ------------------------------------------------- contexto e recomendação
    def criar_contexto(self, dados: dict) -> dict: ...
    def salvar_looks(self, contexto_id: str, looks: list[dict]) -> list[dict]: ...
    def usos_recentes(self) -> dict[str, int]: ...
    def taxa_por_categoria(self) -> dict[str, float]: ...

    # ----------------------------------------------- feedback e personalização
    def parcelas_do_look(self, look_id: str) -> dict | None: ...
    def registrar_feedback(self, look_id: str, aprovado: bool) -> None: ...
    def obter_pesos(self) -> dict[str, float] | None: ...
    def salvar_pesos(self, pesos: dict[str, float]) -> None: ...
    def metricas(self) -> dict: ...


def com_rotulo(linha: dict) -> dict:
    """Acrescenta o nome de exibição da categoria.

    O rótulo não é coluna do banco: vive na taxonomia e muda com ela. Guardar uma
    cópia em cada linha faria peças antigas exibirem nomes desatualizados depois
    de uma revisão da taxonomia.
    """
    categoria = POR_CHAVE.get(linha.get("categoria", ""))
    return {**linha, "rotulo": categoria.rotulo if categoria else linha.get("categoria")}


# ===========================================================================
#  Produção
# ===========================================================================
class RepositorioSupabase:
    def __init__(self, cliente, usuario_id: str):
        self._c = cliente
        self._uid = usuario_id

    # ------------------------------------------------------------------ peças
    def proximo_codigo(self) -> str:
        resposta = self._c.rpc("proximo_codigo_peca", {"p_usuario": self._uid}).execute()
        return resposta.data or "CLO-000001"

    def listar_pecas(self, **filtros: Any) -> list[dict]:
        consulta = self._c.table("pecas").select("*")
        for campo, valor in filtros.items():
            if valor is not None:
                consulta = consulta.eq(campo, valor)
        linhas = consulta.order("criado_em", desc=True).execute().data or []
        return [com_rotulo(l) for l in linhas]

    def criar_peca(self, dados: dict) -> dict:
        linha = {**dados, "usuario_id": self._uid, "codigo": self.proximo_codigo(),
                 "revisada": True}
        return com_rotulo(self._c.table("pecas").insert(linha).execute().data[0])

    def atualizar_peca(self, peca_id: str, campos: dict) -> dict | None:
        resposta = self._c.table("pecas").update(campos).eq("id", peca_id).execute()
        return com_rotulo(resposta.data[0]) if resposta.data else None

    def remover_peca(self, peca_id: str) -> str | None:
        atual = self._c.table("pecas").select("imagem_path").eq("id", peca_id).execute()
        if not atual.data:
            return None
        caminho = atual.data[0].get("imagem_path")
        self._c.table("pecas").delete().eq("id", peca_id).execute()
        if caminho:
            # a imagem sai junto: o RNF11 fala em remoção efetiva, não só do registro
            try:
                self._c.storage.from_("pecas").remove([caminho])
            except Exception:                        # noqa: BLE001
                pass
        return caminho or ""

    # ------------------------------------------------- contexto e recomendação
    def criar_contexto(self, dados: dict) -> dict:
        linha = {**dados, "usuario_id": self._uid}
        return self._c.table("contextos").insert(linha).execute().data[0]

    def salvar_looks(self, contexto_id: str, looks: list[dict]) -> list[dict]:
        """Grava os três looks e seus vínculos em duas chamadas, não em seis.

        A versão anterior fazia um insert por look e outro por conjunto de peças:
        seis idas ao banco dentro do orçamento de 3 s do RNF02. Em lote, são duas.
        """
        registros = [
            {
                "usuario_id": self._uid,
                "contexto_id": contexto_id,
                "posicao": look["posicao"],
                "score": look["score"],
                "parcelas": look["parcelas"],
                "explicacao": look["explicacao"],
            }
            for look in looks
        ]
        salvos = self._c.table("looks").insert(registros).execute().data
        salvos.sort(key=lambda l: l["posicao"])

        vinculos = [
            {"look_id": salvo["id"], "peca_id": peca_id, "papel": papel}
            for salvo, look in zip(salvos, sorted(looks, key=lambda l: l["posicao"]))
            for papel, peca_id in look["pecas"].items()
        ]
        if vinculos:
            self._c.table("look_pecas").insert(vinculos).execute()
        return salvos

    def usos_recentes(self) -> dict[str, int]:
        recentes = (self._c.table("looks").select("id")
                    .order("criado_em", desc=True)
                    .limit(JANELA_VARIEDADE).execute().data or [])
        if not recentes:
            return {}
        vinculos = (self._c.table("look_pecas").select("peca_id")
                    .in_("look_id", [l["id"] for l in recentes]).execute().data or [])
        contagem: dict[str, int] = {}
        for v in vinculos:
            contagem[v["peca_id"]] = contagem.get(v["peca_id"], 0) + 1
        return contagem

    def taxa_por_categoria(self) -> dict[str, float]:
        avaliados = (self._c.table("feedback").select("look_id, aprovado")
                     .order("criado_em", desc=True)
                     .limit(JANELA_PREFERENCIA).execute().data)
        if not avaliados:
            return {}
        aprovacao = {f["look_id"]: f["aprovado"] for f in avaliados}
        vinculos = (self._c.table("look_pecas").select("look_id, pecas(categoria)")
                    .in_("look_id", list(aprovacao)).execute().data or [])
        acumulado: dict[str, list[int]] = {}
        for v in vinculos:
            categoria = (v.get("pecas") or {}).get("categoria")
            if categoria:
                acumulado.setdefault(categoria, []).append(1 if aprovacao[v["look_id"]] else 0)
        return {c: sum(v) / len(v) for c, v in acumulado.items()}

    # ----------------------------------------------- feedback e personalização
    def parcelas_do_look(self, look_id: str) -> dict | None:
        linhas = self._c.table("looks").select("parcelas").eq("id", look_id).execute().data
        return (linhas[0].get("parcelas") or {}) if linhas else None

    def registrar_feedback(self, look_id: str, aprovado: bool) -> None:
        self._c.table("feedback").upsert(
            {"usuario_id": self._uid, "look_id": look_id, "aprovado": aprovado},
            on_conflict="usuario_id,look_id",
        ).execute()

    def obter_pesos(self) -> dict[str, float] | None:
        linhas = (self._c.table("preferencias").select("pesos")
                  .eq("usuario_id", self._uid).execute().data)
        return linhas[0]["pesos"] if linhas else None

    def salvar_pesos(self, pesos: dict[str, float]) -> None:
        self._c.table("preferencias").upsert(
            {"usuario_id": self._uid, "pesos": pesos}, on_conflict="usuario_id",
        ).execute()

    def metricas(self) -> dict:
        linhas = self._c.table("metricas_recomendacao").select("*").execute().data
        return linhas[0] if linhas else _METRICAS_VAZIAS.copy()


_METRICAS_VAZIAS = {
    "consultas": 0, "looks_aprovados": 0, "hit_rate_3": None, "precision_3": None,
}


# ===========================================================================
#  Modo demonstração
# ===========================================================================
# Estado por usuário, vivo enquanto o processo estiver de pé. Reiniciar o uvicorn
# devolve o guarda-roupa de exemplo — comportamento desejado numa demonstração.
_ARMAZENS: dict[str, dict[str, list | dict]] = {}


def _armazem(usuario_id: str) -> dict:
    if usuario_id not in _ARMAZENS:
        _ARMAZENS[usuario_id] = {
            "pecas": _guarda_roupa_exemplo(usuario_id),
            "contextos": [],
            "looks": [],
            "look_pecas": [],
            "feedback": [],
            "pesos": None,
        }
    return _ARMAZENS[usuario_id]


def limpar_armazens() -> None:
    """Zera o estado do modo demonstração. Usado entre testes."""
    _ARMAZENS.clear()


def _peca_exemplo(indice: int, usuario_id: str, categoria: str,
                  cor_nome: str, cor_hex: str, cor_hsv: tuple[float, float, float],
                  neutra: bool) -> dict:
    """Monta uma peça de exemplo herdando papel, formalidade e faixa térmica
    da taxonomia — as mesmas regras que valem para uma peça cadastrada de verdade.
    """
    cat = POR_CHAVE[categoria]
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{usuario_id}/{categoria}/{indice}")),
        "usuario_id": usuario_id,
        "codigo": f"CLO-{indice:06d}",
        "papel": cat.papel,
        "categoria": categoria,
        "atributos": {},
        "cor_nome": cor_nome,
        "cor_hex": cor_hex,
        "cor_hsv": list(cor_hsv),
        "neutra": neutra,
        "formalidade": cat.formalidade,
        "temp_min": cat.temp_min,
        "temp_max": cat.temp_max,
        "resiste_chuva": cat.resiste_chuva,
        "disponivel": True,
        "imagem_path": None,
        "confianca": {},
        "revisada": True,
        "criado_em": _agora(),
    }


def _guarda_roupa_exemplo(usuario_id: str) -> list[dict]:
    """Guarda-roupa mínimo que cobre calor, frio e as cinco faixas de formalidade.

    Sem isto, a primeira coisa que o usuário vê ao abrir a demonstração é uma tela
    vazia dizendo que faltam peças — o que esconde justamente a funcionalidade
    principal.
    """
    modelos = [
        ("camiseta",      "branca",  "#f2f2f0", (0, 0.01, 0.95), True),
        ("camiseta",      "preta",   "#1a1a1a", (0, 0.00, 0.10), True),
        ("polo",          "azul",    "#2f5f9e", (213, 0.70, 0.62), False),
        ("camisa-casual", "marrom",  "#7a5c48", (25, 0.41, 0.48), True),
        ("camisa-social", "branca",  "#f7f7f5", (0, 0.01, 0.97), True),
        ("sueter",        "cinza",   "#8a8a88", (60, 0.02, 0.54), True),
        ("bermuda",       "bege",    "#c9b79a", (37, 0.23, 0.79), True),
        ("calca-jeans",   "azul",    "#3c5a80", (213, 0.53, 0.50), False),
        ("calca-sarja",   "bege",    "#b8a888", (42, 0.26, 0.72), True),
        ("calca-social",  "preta",   "#17171a", (240, 0.06, 0.10), True),
        ("tenis",         "branco",  "#eeeeec", (60, 0.01, 0.93), True),
        ("tenis-casual",  "preto",   "#1d1d1d", (0, 0.00, 0.11), True),
        ("sapato-social", "marrom",  "#5a3a22", (25, 0.62, 0.35), True),
        ("chinelo",       "preto",   "#212121", (0, 0.00, 0.13), True),
        ("jaqueta-jeans", "azul",    "#41618a", (214, 0.53, 0.54), False),
        ("blazer",        "marinho", "#22304d", (222, 0.56, 0.30), True),
    ]
    return [
        _peca_exemplo(i, usuario_id, *modelo)
        for i, modelo in enumerate(modelos, start=1)
    ]


class RepositorioMemoria:
    """Implementação de demonstração. Mesma semântica, sem rede."""

    def __init__(self, usuario_id: str):
        self._uid = usuario_id
        self._d = _armazem(usuario_id)

    # ------------------------------------------------------------------ peças
    def proximo_codigo(self) -> str:
        return f"CLO-{len(self._d['pecas']) + 1:06d}"

    def listar_pecas(self, **filtros: Any) -> list[dict]:
        pecas = [
            p for p in self._d["pecas"]
            if all(p.get(campo) == valor
                   for campo, valor in filtros.items() if valor is not None)
        ]
        pecas.sort(key=lambda p: p["criado_em"], reverse=True)
        return [com_rotulo(p) for p in pecas]

    def criar_peca(self, dados: dict) -> dict:
        linha = {
            **dados,
            "id": str(uuid.uuid4()),
            "usuario_id": self._uid,
            "codigo": self.proximo_codigo(),
            "disponivel": True,
            "revisada": True,
            "criado_em": _agora(),
        }
        self._d["pecas"].append(linha)
        return com_rotulo(linha)

    def _buscar_peca(self, peca_id: str) -> dict | None:
        return next((p for p in self._d["pecas"] if p["id"] == peca_id), None)

    def atualizar_peca(self, peca_id: str, campos: dict) -> dict | None:
        peca = self._buscar_peca(peca_id)
        if peca is None:
            return None
        peca.update(campos)
        return com_rotulo(peca)

    def remover_peca(self, peca_id: str) -> str | None:
        peca = self._buscar_peca(peca_id)
        if peca is None:
            return None
        self._d["pecas"].remove(peca)
        return peca.get("imagem_path") or ""

    # ------------------------------------------------- contexto e recomendação
    def criar_contexto(self, dados: dict) -> dict:
        linha = {**dados, "id": str(uuid.uuid4()), "usuario_id": self._uid,
                 "criado_em": _agora()}
        self._d["contextos"].append(linha)
        return linha

    def salvar_looks(self, contexto_id: str, looks: list[dict]) -> list[dict]:
        salvos = []
        for look in sorted(looks, key=lambda l: l["posicao"]):
            linha = {
                "id": str(uuid.uuid4()),
                "usuario_id": self._uid,
                "contexto_id": contexto_id,
                "posicao": look["posicao"],
                "score": look["score"],
                "parcelas": look["parcelas"],
                "explicacao": look["explicacao"],
                "criado_em": _agora(),
            }
            self._d["looks"].append(linha)
            for papel, peca_id in look["pecas"].items():
                self._d["look_pecas"].append(
                    {"look_id": linha["id"], "peca_id": peca_id, "papel": papel})
            salvos.append(linha)
        return salvos

    def usos_recentes(self) -> dict[str, int]:
        recentes = sorted(self._d["looks"], key=lambda l: l["criado_em"],
                          reverse=True)[:JANELA_VARIEDADE]
        ids = {l["id"] for l in recentes}
        contagem: dict[str, int] = {}
        for v in self._d["look_pecas"]:
            if v["look_id"] in ids:
                contagem[v["peca_id"]] = contagem.get(v["peca_id"], 0) + 1
        return contagem

    def taxa_por_categoria(self) -> dict[str, float]:
        recentes = sorted(self._d["feedback"], key=lambda f: f["criado_em"],
                          reverse=True)[:JANELA_PREFERENCIA]
        aprovacao = {f["look_id"]: f["aprovado"] for f in recentes}
        if not aprovacao:
            return {}
        por_id = {p["id"]: p for p in self._d["pecas"]}
        acumulado: dict[str, list[int]] = {}
        for v in self._d["look_pecas"]:
            if v["look_id"] not in aprovacao:
                continue
            peca = por_id.get(v["peca_id"])
            if peca:
                acumulado.setdefault(peca["categoria"], []).append(
                    1 if aprovacao[v["look_id"]] else 0)
        return {c: sum(v) / len(v) for c, v in acumulado.items()}

    # ----------------------------------------------- feedback e personalização
    def parcelas_do_look(self, look_id: str) -> dict | None:
        look = next((l for l in self._d["looks"] if l["id"] == look_id), None)
        return (look.get("parcelas") or {}) if look else None

    def registrar_feedback(self, look_id: str, aprovado: bool) -> None:
        anterior = next((f for f in self._d["feedback"] if f["look_id"] == look_id), None)
        if anterior:
            anterior["aprovado"] = aprovado
        else:
            self._d["feedback"].append(
                {"look_id": look_id, "aprovado": aprovado, "criado_em": _agora()})

    def obter_pesos(self) -> dict[str, float] | None:
        return self._d["pesos"]

    def salvar_pesos(self, pesos: dict[str, float]) -> None:
        self._d["pesos"] = pesos

    def metricas(self) -> dict:
        """Mesmo cálculo da view SQL `metricas_recomendacao`, em Python.

        Hit Rate@3 conta *consultas* com ao menos um look aprovado; Precision@3
        conta *looks* aprovados entre os avaliados. São coisas diferentes, e
        confundi-las é o erro clássico ao relatar o RNF04.
        """
        aprovacao = {f["look_id"]: f["aprovado"] for f in self._d["feedback"]}
        consultas = len(self._d["contextos"])
        avaliados = [a for a in aprovacao.values()]
        aprovados = sum(1 for a in avaliados if a)

        por_contexto: dict[str, bool] = {}
        for look in self._d["looks"]:
            if aprovacao.get(look["id"]):
                por_contexto[look["contexto_id"]] = True

        return {
            "consultas": consultas,
            "looks_aprovados": aprovados,
            "hit_rate_3": (len(por_contexto) / consultas) if consultas else None,
            "precision_3": (aprovados / len(avaliados)) if avaliados else None,
        }
