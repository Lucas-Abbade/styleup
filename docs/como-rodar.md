# Como rodar o StyleUp

Três jeitos, do mais simples ao completo.

| Modo | Precisa de | Para quê |
|---|---|---|
| Demonstração | Python e Node | Ver o sistema, desenvolver o front, apresentar sem rede |
| Real, sem visão | + projeto no Supabase | Usar com dados reais, cadastrando as peças à mão |
| Real, completo | + `requirements-visao.txt` (~2 GB) | Catalogação automática por foto |

## 1. Modo demonstração

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                 # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Abra http://localhost:5173, toque em **Começar** e entre com qualquer e-mail.
A API avisa no log: `MODO DEMONSTRAÇÃO: dados em memória e login fictício`. Os dados
somem quando a API reinicia. `POST /demo/reiniciar` devolve o guarda-roupa de exemplo.

O modo liga sozinho quando `SUPABASE_URL`/`SUPABASE_ANON_KEY` não estão definidos (na
API) e quando `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` não estão definidos (no
front). **Os dois lados precisam estar no mesmo modo.** Com `AMBIENTE=producao` ele
nunca liga.

## 2. Modo real (Supabase)

### 2.1 Banco

No painel do Supabase, em **SQL Editor**, execute os arquivos de
`supabase/migrations/` **em ordem**, um de cada vez:

1. `0001_schema.sql`
2. `0002_rls.sql`
3. `0003_privacidade_e_conta.sql`
4. `0004_codigo_metricas_e_validacoes.sql`
5. `0005_looks_estilo_e_acessorios.sql`

Quem já tem o banco com a 0001 e a 0002 executa só da 0003 em diante. Cada arquivo
começa com uma nota de **impacto nos dados existentes** — leia antes de executar. As
três novas podem ser executadas mais de uma vez sem erro, e cada uma tem o script
correspondente em `supabase/migrations/reverter/` (reverta na ordem 0005 → 0004 → 0003).

Para testar as migrações antes de tocar no Supabase (precisa do PostgreSQL 15+
instalado na máquina):

```bash
./supabase/testes/rodar.sh
```

### 2.2 Variáveis de ambiente

Raiz do projeto, arquivo `.env` (copie de `.env.example`):

```
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<chave anon / publishable>
SUPABASE_JWT_SECRET=<só se o projeto ainda assina com HS256>
ORIGENS_PERMITIDAS=http://localhost:5173
```

`frontend/.env.local` (copie de `frontend/.env.example`):

```
VITE_SUPABASE_URL=https://<seu-projeto>.supabase.co
VITE_SUPABASE_ANON_KEY=<a mesma chave anon>
VITE_API_URL=http://localhost:8000
```

Carregue o `.env` ao subir a API:

```bash
uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

Confira em http://localhost:8000/saude: `supabase_configurado: true` e `modo_demo: false`.

### 2.3 Visão (catalogação por foto)

```bash
pip install -r requirements-visao.txt
```

Na primeira subida a API baixa os modelos (rembg/U²-Net e FashionCLIP) em segundo
plano. Acompanhe em `/saude`: `visao.situacao` passa de `aquecendo` para `pronto` (com o
tempo que levou). Enquanto isso o resto da API responde normalmente. Depois do primeiro
download, o aquecimento leva segundos.

Para apresentar: suba a API alguns minutos antes e confira `pronto` no `/saude`.

## 3. Docker

O `docker-compose.yml` sobe **só a API** (com as dependências de visão e um volume para
o cache dos modelos); o front continua com `npm run dev` ou `npm run build`.

```bash
docker compose up --build
```

## 4. Antes de testar com usuários reais

- [ ] Trocar o JWT secret que apareceu em print (painel do Supabase → Project Settings →
      JWT Keys: migrar para *signing keys*, rotacionar e revogar o segredo antigo). Isso
      encerra as sessões abertas; a chave anon antiga deixa de valer e precisa ser
      atualizada nos dois `.env`.
- [ ] Preencher `CONTROLADOR` e `CONTATO` em `backend/app/termo.py` e revisar o texto do
      termo com o orientador.
- [ ] Rodar `python -m scripts.medir_tempos` e `python -m scripts.medir_acuracia` e
      registrar os números.

## 5. Problemas comuns

**"Para continuar, leia e aceite o termo" (403 `consentimento_pendente`)** — é o
comportamento esperado para quem ainda não aceitou a versão vigente do termo. O app
mostra a tela sozinho. Para desligar em desenvolvimento: `EXIGIR_CONSENTIMENTO=false`.

**"O banco de dados está desatualizado" (500 `migracao_pendente`)** — falta executar
alguma migração (0003 a 0005).

**"Token de acesso inválido" logo após configurar** — confira se `SUPABASE_URL` da API é
o mesmo projeto do front (a API valida o emissor do token) e, em projeto HS256, se o
`SUPABASE_JWT_SECRET` está correto. O motivo exato aparece no log da API.

**Variável de ambiente antiga atrapalhando (Windows)** — uma variável definida no
sistema vence o `.env`. Veja com `echo %SUPABASE_URL%` e remova com
`setx SUPABASE_URL ""` (abra outro terminal depois). Cuidado ao colar chaves: um
caractere acentuado ou espaço no fim invalida a chave.

**O front abre em modo demonstração mesmo com o Supabase configurado** — o Vite só lê
`frontend/.env.local` ao iniciar: pare e rode `npm run dev` de novo.

**Fotos não aparecem** — confira se o bucket `pecas` existe e é privado (a 0002 cria) e
se a foto foi enviada para a pasta `<id do usuário>/`.

**Porta em uso** — `uvicorn ... --port 8001` e ajuste `VITE_API_URL`.
