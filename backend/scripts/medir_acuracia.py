"""Mede a acurácia da catalogação automática num conjunto de fotos rotuladas.

Uso (na pasta backend/, com requirements-visao.txt instalado):

    python -m scripts.medir_acuracia                       # usa avaliacao/
    python -m scripts.medir_acuracia --pasta minha_pasta --saida relatorio

Formato esperado
----------------
    avaliacao/
      rotulos.csv
      fotos/
        camiseta_preta_01.jpg
        ...

`rotulos.csv` (UTF-8, separado por vírgula, com cabeçalho):

    arquivo,categoria,cor,estilo,manga,estampa
    camiseta_preta_01.jpg,camiseta,preto,esportivo,curta,lisa
    calca_jeans_02.jpg,calca-jeans,azul,casual,,lisa

* `arquivo`   — nome do arquivo dentro de fotos/ (obrigatório)
* `categoria` — chave da taxonomia: camiseta, polo, calca-jeans, tenis… (obrigatório)
* `cor`       — nome de cor do sistema: preto, grafite, marinho, verde-oliva… (obrigatório)
* `estilo`    — nível de formalidade: esportivo, casual, casual-arrumado, social, formal
* `manga`     — curta | longa          (vazio = não se aplica)
* `estampa`   — lisa | listrada | estampada | xadrez   (vazio = não avaliar)

`python -m scripts.medir_acuracia --valores` lista os valores aceitos em cada coluna.

Saída: `<saida>.md` (para o relatório e o slide) e `<saida>.json` (dados brutos,
uma linha por foto, para auditoria). O intervalo de confiança é o de Wilson a
95% — com 50 a 100 fotos, um número sozinho engana; a faixa mostra o quanto.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

from app.services.cor import NOMES_CONHECIDOS
from app.services.taxonomia import ATRIBUTOS, POR_CHAVE

ESTILOS = {"esportivo": 1, "casual": 2, "casual-arrumado": 3, "social": 4, "formal": 5}
ATRIBUTOS_MEDIDOS = ("categoria", "cor", "estilo", "manga", "estampa")
METAS = {"categoria": 0.90, "cor": 0.85}        # RNF03


def wilson(acertos: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de Wilson para uma proporção."""
    if total == 0:
        return 0.0, 0.0
    p = acertos / total
    denominador = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)


def ler_rotulos(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = [{k.strip(): (v or "").strip() for k, v in linha.items() if k}
                  for linha in csv.DictReader(arquivo)]
    problemas = []
    for n, linha in enumerate(linhas, start=2):
        if not linha.get("arquivo"):
            problemas.append(f"linha {n}: coluna 'arquivo' vazia")
        if linha.get("categoria") not in POR_CHAVE:
            problemas.append(f"linha {n}: categoria desconhecida '{linha.get('categoria')}'")
        if linha.get("cor") not in NOMES_CONHECIDOS:
            problemas.append(f"linha {n}: cor desconhecida '{linha.get('cor')}'")
        if linha.get("estilo") and linha["estilo"] not in ESTILOS:
            problemas.append(f"linha {n}: estilo desconhecido '{linha['estilo']}'")
        for atributo in ("manga", "estampa"):
            if linha.get(atributo) and linha[atributo] not in ATRIBUTOS[atributo]:
                problemas.append(f"linha {n}: {atributo} desconhecida '{linha[atributo]}'")
    if problemas:
        raise ValueError("rotulos.csv com problemas:\n  " + "\n  ".join(problemas[:20]))
    return linhas


def _previsto(analise: dict) -> dict:
    return {
        "categoria": analise["categoria"],
        "cor": analise["cor_nome"],
        "estilo": next(k for k, v in ESTILOS.items() if v == analise["formalidade"]),
        "manga": analise.get("atributos", {}).get("manga", ""),
        "estampa": analise.get("atributos", {}).get("estampa", ""),
    }


def avaliar(rotulos: list[dict], pasta_fotos: Path,
            analisar: Callable[[bytes], dict]) -> dict:
    """Roda a análise em cada foto e compara com o rótulo. Não imprime nada."""
    fotos, falhas, tempos = [], [], []
    for linha in rotulos:
        caminho = pasta_fotos / linha["arquivo"]
        if not caminho.is_file():
            falhas.append({"arquivo": linha["arquivo"], "motivo": "arquivo não encontrado"})
            continue
        inicio = time.perf_counter()
        try:
            analise = analisar(caminho.read_bytes())
        except Exception as exc:                 # noqa: BLE001 — a falha é um resultado
            falhas.append({"arquivo": linha["arquivo"], "motivo": str(exc)})
            continue
        tempos.append(time.perf_counter() - inicio)
        previsto = _previsto(analise)
        fotos.append({
            "arquivo": linha["arquivo"],
            "esperado": {a: linha.get(a, "") for a in ATRIBUTOS_MEDIDOS},
            "previsto": previsto,
            "top3": list(analise.get("confianca", {})),
            "confianca_baixa": bool(analise.get("confianca_baixa")),
            "segundos": round(tempos[-1], 3),
        })

    resumo = {}
    for atributo in ATRIBUTOS_MEDIDOS:
        avaliadas = [f for f in fotos if f["esperado"][atributo]]
        acertos = sum(f["esperado"][atributo] == f["previsto"][atributo] for f in avaliadas)
        baixo, alto = wilson(acertos, len(avaliadas))
        por_classe: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        confusoes: Counter = Counter()
        for f in avaliadas:
            esperado, obtido = f["esperado"][atributo], f["previsto"][atributo]
            por_classe[esperado][1] += 1
            if esperado == obtido:
                por_classe[esperado][0] += 1
            else:
                confusoes[(esperado, obtido)] += 1
        resumo[atributo] = {
            "avaliadas": len(avaliadas), "acertos": acertos,
            "acuracia": round(acertos / len(avaliadas), 4) if avaliadas else None,
            "ic95": [round(baixo, 4), round(alto, 4)],
            "meta": METAS.get(atributo),
            "por_classe": {c: {"acertos": a, "total": t} for c, (a, t) in sorted(por_classe.items())},
            "confusoes": [{"esperado": e, "previsto": p, "vezes": n}
                          for (e, p), n in confusoes.most_common(10)],
        }
    com_top3 = [f for f in fotos if f["top3"]]
    resumo["categoria"]["top3"] = (
        round(sum(f["esperado"]["categoria"] in f["top3"] for f in com_top3) / len(com_top3), 4)
        if com_top3 else None)

    return {
        "total_rotuladas": len(rotulos), "analisadas": len(fotos), "falhas": falhas,
        "tempo": {
            "mediana_s": round(statistics.median(tempos), 3) if tempos else None,
            "p95_s": round(sorted(tempos)[max(0, math.ceil(0.95 * len(tempos)) - 1)], 3)
                     if tempos else None,
            "max_s": round(max(tempos), 3) if tempos else None,
        },
        "confianca_baixa": sum(f["confianca_baixa"] for f in fotos),
        "atributos": resumo, "fotos": fotos,
    }


def _pct(valor: float | None) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%".replace(".", ",")


def relatorio_markdown(r: dict) -> str:
    linhas = [
        "# Acurácia da catalogação automática", "",
        f"Fotos rotuladas: **{r['total_rotuladas']}** · analisadas: **{r['analisadas']}** · "
        f"falhas: **{len(r['falhas'])}** · marcadas como baixa confiança: "
        f"**{r['confianca_baixa']}**", "",
        "| Atributo | Avaliadas | Acertos | Acurácia | IC 95% (Wilson) | Meta | Situação |",
        "|---|---:|---:|---:|---|---:|---|",
    ]
    for atributo in ATRIBUTOS_MEDIDOS:
        a = r["atributos"][atributo]
        if a["meta"] is None or a["acuracia"] is None:
            situacao = "—"
        elif a["ic95"][0] >= a["meta"]:
            situacao = "atinge"
        elif a["ic95"][1] < a["meta"]:
            situacao = "não atinge"
        else:
            situacao = "inconclusivo (amostra pequena)"
        linhas.append(
            f"| {atributo} | {a['avaliadas']} | {a['acertos']} | {_pct(a['acuracia'])} | "
            f"{_pct(a['ic95'][0])} – {_pct(a['ic95'][1])} | {_pct(a['meta'])} | {situacao} |")
    linhas += ["", f"Categoria entre as 3 mais prováveis (top-3): "
                   f"**{_pct(r['atributos']['categoria']['top3'])}**", ""]
    t = r["tempo"]
    if t["mediana_s"] is not None:
        linhas += [f"Tempo por foto: mediana **{t['mediana_s']} s**, p95 **{t['p95_s']} s**, "
                   f"máximo **{t['max_s']} s** (meta do RNF01: 5 s).", ""]
    for atributo in ("categoria", "cor"):
        a = r["atributos"][atributo]
        linhas += [f"## {atributo.capitalize()} por classe", "",
                   "| Classe | Acertos | Total | Acurácia |", "|---|---:|---:|---:|"]
        linhas += [f"| {c} | {v['acertos']} | {v['total']} | {_pct(v['acertos'] / v['total'])} |"
                   for c, v in a["por_classe"].items()]
        if a["confusoes"]:
            linhas += ["", "Confusões mais frequentes:", ""]
            linhas += [f"- {c['esperado']} → classificada como **{c['previsto']}** ({c['vezes']}×)"
                       for c in a["confusoes"]]
        linhas.append("")
    if r["falhas"]:
        linhas += ["## Fotos que não puderam ser analisadas", ""]
        linhas += [f"- `{f['arquivo']}` — {f['motivo']}" for f in r["falhas"]]
        linhas.append("")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    opcoes = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    opcoes.add_argument("--pasta", default="avaliacao", help="pasta com rotulos.csv e fotos/")
    opcoes.add_argument("--saida", default=None, help="prefixo dos arquivos de saída")
    opcoes.add_argument("--valores", action="store_true",
                        help="lista os valores aceitos em cada coluna e sai")
    args = opcoes.parse_args(argv)

    if args.valores:
        print("categoria:", ", ".join(POR_CHAVE))
        print("cor:", ", ".join(NOMES_CONHECIDOS))
        print("estilo:", ", ".join(ESTILOS))
        for nome, valores in ATRIBUTOS.items():
            print(f"{nome}:", ", ".join(valores))
        return 0

    pasta = Path(args.pasta)
    try:
        rotulos = ler_rotulos(pasta / "rotulos.csv")
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    if not rotulos:
        print("rotulos.csv não tem nenhuma foto rotulada.", file=sys.stderr)
        return 2

    from app.services import visao
    print("Carregando os modelos…", file=sys.stderr)
    visao.aquecer()
    if visao.estado()["situacao"] != "pronto":
        print("Modelos indisponíveis:", visao.estado()["detalhe"], file=sys.stderr)
        return 3

    resultado = avaliar(rotulos, pasta / "fotos",
                        lambda dados: visao.analisar(dados, com_recorte=False))
    prefixo = Path(args.saida or pasta / "relatorio")
    prefixo.with_suffix(".json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    texto = relatorio_markdown(resultado)
    prefixo.with_suffix(".md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
