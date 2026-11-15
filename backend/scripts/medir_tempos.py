"""Mede os tempos de resposta da API no ambiente real (RNF01 e RNF02).

Uso (na pasta backend/, com a API no ar):

    python -m scripts.medir_tempos --token <JWT do usuário> [--foto peca.jpg]
    python -m scripts.medir_tempos --token demo            # modo demonstração

O tempo vem do cabeçalho X-Tempo-ms, medido dentro do servidor (não inclui a
rede até o cliente). Para o JWT: entre no app, abra as ferramentas do navegador
e copie o valor de Authorization de qualquer chamada à API — sem o "Bearer ".
"""

from __future__ import annotations

import argparse
import statistics
import sys

import httpx


def resumo(nome: str, tempos: list[float]) -> str:
    ordenados = sorted(tempos)
    p95 = ordenados[max(0, round(0.95 * len(ordenados)) - 1)]
    return (f"{nome:<34} n={len(tempos):<3} mediana={statistics.median(tempos):7.0f} ms  "
            f"p95={p95:7.0f} ms  máx={ordenados[-1]:7.0f} ms")


def main() -> int:
    opcoes = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    opcoes.add_argument("--url", default="http://localhost:8000")
    opcoes.add_argument("--token", required=True)
    opcoes.add_argument("--repeticoes", type=int, default=10)
    opcoes.add_argument("--foto", help="foto de uma peça, para medir a catalogação")
    opcoes.add_argument("--latitude", type=float)
    opcoes.add_argument("--longitude", type=float)
    args = opcoes.parse_args()

    cabecalho = {"Authorization": f"Bearer {args.token}"}
    with httpx.Client(base_url=args.url, headers=cabecalho, timeout=180) as api:
        saude = api.get("/saude").json()
        print(f"API: {args.url} · modo demonstração: {saude['modo_demo']} · "
              f"visão: {saude['visao']['situacao']}")

        def medir(nome: str, chamar) -> None:
            tempos = []
            for _ in range(args.repeticoes):
                resposta = chamar()
                if resposta.status_code >= 400:
                    print(f"{nome}: HTTP {resposta.status_code} — {resposta.text[:200]}")
                    return
                tempos.append(float(resposta.headers["x-tempo-ms"]))
            print(resumo(nome, tempos))

        medir("GET /pecas", lambda: api.get("/pecas"))
        pedido = {"evento": "casual", "temperatura": 28}
        medir("POST /recomendacoes (clima manual)", lambda: api.post("/recomendacoes", json=pedido))
        if args.latitude is not None and args.longitude is not None:
            local = {"evento": "casual", "latitude": args.latitude, "longitude": args.longitude}
            medir("POST /recomendacoes (clima da API)", lambda: api.post("/recomendacoes", json=local))
        if args.foto:
            dados = open(args.foto, "rb").read()
            medir("POST /pecas/analisar", lambda: api.post(
                "/pecas/analisar", files={"foto": ("foto.jpg", dados, "image/jpeg")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
