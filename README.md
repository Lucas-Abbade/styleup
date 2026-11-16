# StyleUp

Sistema de catalogação de vestuário masculino por oto, com recomendação de looksconforme clima e ocasião. Projeto da disciplina de Projeto de Software — Engenharia
de Computação e Automação, UFMT.

## Como funciona

```
┌────────────┐  foto   ┌──────────────────────────┐        ┌───────────────┐
│  Frontend  │────────▶│         FastAPI          │───────▶│   Supabase    │
│ React/PWA  │◀────────│ visão · motor · feedback │◀───────│ Postgres+Auth │
└─────┬──────┘ looks   └────────────┬─────────────┘        │ +Storage (RLS)│
      │ recorte da peça             │                      └───────────────┘
      └──────────────────────────▶ Storage     Open-Meteo (clima, sem chave)
```

| Módulo | Onde está | O que faz |
|---|---|---|
| M1–M2 catalogação | `backend/app/services/visao.py`, `cor.py` | Recorta a peça, classifica (FashionCLIP zero-shot) e nomeia a cor |
| M3 guarda-roupa | `backend/app/routers/pecas.py` |
 Cadastro, edição, disponibilidade e remoção (com a foto) |
| M4 contexto | `services/clima.py`, `interpretacao.py` | Clima (Open-Meteo, em cache) e leitura do pedido em texto livre |
 M5 recomendação | `services/recomendador.py` | Filtros → combinações → score de 5 critérios → 3 looks diversos |
| M6 explicação e feedback | `services/explicacao.py`, `routers/feedback.py` | Justificativa por template e ajuste dos pesos |
| Privacidade (LGPD) | `routers/perfil.py`, `termo.py` | Consentimento, exportação e exclusão da conta |
| Acesso a dados | `backend/app/repositorio/` | Supabase (um cliente por requisição) ou memória (demonstração e testes) |

## Rodando em 2 minutos (modo demonstração, sem Supabase)

Sem nenhuma chave configurada, a API guarda os dados em memória e o app entra com
qualquer e-mail, já com um guarda-roupa de exemplo. É o jeito mais rápido de ver o
sistema e o mais seguro para apresentar num auditório sem depender de rede.

```bash
# terminal 1 — API
cd backend
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# terminal 2 — app
cd frontend
npm install
npm run dev                                           # http://localhost:5173
```

A análise de foto precisa das dependências de visão (`pip install -r
requirements-visao.txt`, ~2 GB). Sem elas o cadastro continua funcionando, com
preenchimento manual.

## Rodando com o Supabase (dados reais)

O passo a passo completo — projeto no Supabase, migrações, variáveis de ambiente e
problemas comuns — está em **[docs/como-rodar.md](docs/como-rodar.md)**.

Resumo: aplique `supabase/migrations/0001` a `0005` em ordem, copie `.env.example`
para `.env` (raiz) e `frontend/.env.example` para `frontend/.env.local`, preencha e
suba os dois processos como acima.

## Testes

```bash
cd backend && pytest                 # 186 testes: motor, rotas, defeitos corrigidos, LGPD
./supabase/testes/rodar.sh           # migrações num Postgres local descartável
cd frontend && npx tsc --noEmit && npm run build
python frontend/e2e/fluxo_demo.py    # fluxo completo no navegador (modo demonstração)
```

Medições (ver `backend/avaliacao/LEIA-ME.md`):

```bash
cd backend
python -m scripts.medir_acuracia                 # acurácia em fotos rotuladas (RNF03)
python -m scripts.medir_tempos --token <JWT>     # tempos de resposta (RNF01, RNF02)
```

## Documentos

- [docs/como-rodar.md](docs/como-rodar.md) — instalação e operação
- [docs/relatorio-de-melhorias.md](docs/relatorio-de-melhorias.md) — o que mudou nesta
  revisão, mudanças de comportamento da API, medições e pendências do time
- [docs/atualizar-documento-de-visao.md](docs/atualizar-documento-de-visao.md)

## Requisitos não funcionais

| RNF | Como é atendido | Situação |
|---|---|---|
| RNF01 catalogação < 5 s | modelos aquecidos na subida, textos codificados uma vez, foto reduzida no aparelho | medir com `medir_tempos` no ambiente real |
| RNF02 recomendação < 3 s | 5 idas ao banco (eram 13), clima em cache, pré-filtro do motor | medir com `medir_tempos` no ambiente real |
| RNF03 acurácia | fundo branco, ensemble de prompts, sinal de baixa confiança | medir com `medir_acuracia` em 50–100 fotos |
| RNF04 Hit Rate@3 / Precision@3 | view por usuário no banco, exposta em `/metricas` e no Perfil | pronto |
| RNF05 cor em texto | nome da cor ao lado de toda amostra | pronto |
| RNF06 PWA instalável | `vite-plugin-pwa` | pronto |
| RNF07 degradação | clima manual; filtros afrouxados com aviso; cadastro sem análise | pronto |
| RNF09 consulta sem rede | cópia local do guarda-roupa por usuário | pronto |
| RNF11 remoção efetiva | foto apagada e conferida; exclusão de conta apaga a pasta do bucket | pronto |
| RNF12 isolamento | RLS + cliente por requisição com o JWT do usuário | pronto |
| RNF14 sem dependência paga | Open-Meteo, modelos abertos, explicação por template | pronto |
