# Guia do time StyleUp

Como rodar, como o sistema funciona por dentro, o que editar para mudar cada
coisa, e o que cabe a cada integrante. Leia a sua seção antes de abrir o código.

---

## 1. Como rodar

### 1.1 Caminho mais curto (sem configurar nada)

Precisa de **Python 3.11+** e **Node 18+**. Nenhuma conta, nenhuma chave.

**Terminal 1 — API**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt    # ~30 s
uvicorn app.main:app --reload --port 8000
```

Confirme no log:

```
WARNING styleup | API em MODO DEMONSTRACAO (credenciais do Supabase ausentes):
dados em memoria, autenticacao desligada e guarda-roupa de exemplo carregado.
```

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

Abra <http://localhost:5173>, escolha um compromisso, clique em **Recomendar**.

| Endereço | O que é |
|---|---|
| <http://localhost:5173> | a aplicação |
| <http://localhost:8000/docs> | documentação interativa da API, com botão de testar |
| <http://localhost:8000/saude> | em que modo a API subiu, e se o modelo de visão está instalado |

**No celular, na mesma rede:** `npm run dev -- --host` e acesse `http://<IP-da-máquina>:5173`.
Descubra o IP com `ipconfig` (Windows) ou `ip addr` (Linux).

### 1.2 Docker (a pilha inteira num comando)

```bash
docker compose up --build
```

- frontend: <http://localhost:8080>
- API: <http://localhost:8000/docs>

O `docker-compose.yml` sobe a imagem sem o modelo de visão (`COM_VISAO: "false"`),
o que deixa a imagem em ~200 MB em vez de ~2,5 GB. Para incluir o modelo, troque
esse argumento e reconstrua.

> Não consegui construir estas imagens no ambiente onde escrevi o código (não
> havia daemon do Docker). O `docker-compose.yml` está validado como YAML e a
> configuração do nginx foi testada servindo o build de verdade — mas **o
> primeiro `docker compose up --build` de vocês é a primeira execução real**.
> Se falhar, o erro provável está no `npm ci` do `frontend/Dockerfile`: confirme
> que o `package-lock.json` está commitado.

### 1.3 Rodar os testes

```bash
cd backend
python -m pytest                                  # 180 testes, ~1 s, sem rede
python -m pytest --cov=app --cov-report=term       # com cobertura (90%)
python -m pytest tests/test_recomendador.py -v     # só o motor, com nomes
python -m pytest -k "chuva"                        # só o que casa com "chuva"
```

Se a suíte demorar mais de uns segundos ou pedir rede, algo está errado: ela é
inteiramente local por construção.

### 1.4 Ligar o Supabase (quando for para o ar)

1. Crie um projeto em <https://supabase.com> (plano gratuito basta).
2. **SQL Editor** → cole e execute, nesta ordem:
   - `supabase/migrations/0001_schema.sql`
   - `supabase/migrations/0002_rls.sql`
   - `supabase/migrations/0003_indices_e_seguranca.sql`
3. **Project Settings → API**: copie a **URL**, a **anon key** e o **JWT Secret**.
4. Na raiz: `cp .env.example .env` e preencha.
5. Em `frontend/`: `cp .env.example .env.local` e preencha.
6. Reinicie a API. O log passa a dizer `conectada ao Supabase`, o login aparece
   e a faixa de demonstração desaparece.

Para mexer no frontend sem sujar os dados reais: `MODO_DEMO=true` no `.env`.

### 1.5 Habilitar a análise de foto (opcional, ~2 GB)

Sem isto o cadastro por foto **continua funcionando**: a cor é medida de verdade
na imagem (k-means sobre a máscara, só numpy) e a categoria vem como palpite
para confirmar na tela. Só quem for mexer em visão computacional precisa:

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu   # ~200 MB
pip install -r requirements-visao.txt
```

---

## 2. Mapa do código

### Backend (`backend/app/`)

| Arquivo | O que faz | Quando você mexe |
|---|---|---|
| `main.py` | cria a aplicação, CORS, middleware de tempo, `/saude` | quase nunca |
| `config.py` | lê o ambiente, decide demonstração vs Supabase | ao adicionar variável de ambiente |
| `auth.py` | valida o JWT do Supabase | quase nunca |
| `db.py` | escolhe e entrega o repositório da requisição | quase nunca |
| `erros.py` | tratamento global: envelope, tradução, id de requisição | ao adicionar mensagem de erro nova |
| `repositorio.py` | **camada de dados**: interface + Supabase + memória | ao adicionar tabela ou consulta |
| `schemas.py` | contratos de entrada e saída (Pydantic) | ao mudar qualquer campo da API |
| `routers/pecas.py` | catalogação e guarda-roupa (seções 6.2 e 6.3) | ao adicionar rota de peça |
| `routers/recomendacao.py` | contexto e recomendação (6.4 e 6.5) | ao mudar o fluxo principal |
| `routers/feedback.py` | feedback e métricas (6.6) | ao mudar a personalização |
| `services/taxonomia.py` | **as regras de vestuário**: 24 categorias, formalidade, faixa térmica | ao adicionar peça ou ajustar regra |
| `services/recomendador.py` | **o motor**: filtros, score, ranqueamento | ao mudar como o sistema decide |
| `services/cor.py` | k-means, nomeação de cor, harmonia | ao ajustar regra de cor |
| `services/explicacao.py` | o texto que justifica cada look | ao mudar a redação |
| `services/visao.py` | pipeline de visão (rembg + FashionCLIP) | ao mexer em M1/M2 |
| `services/clima.py` | Open-Meteo, com cache | quase nunca |

**Dois arquivos concentram a inteligência do produto:** `taxonomia.py` (o que o
sistema sabe sobre roupa) e `recomendador.py` (como ele decide). Ambos são puros
— sem banco, sem rede — e por isso 100% testáveis. Comece por eles.

### Frontend (`frontend/src/`)

| Arquivo | O que faz |
|---|---|
| `main.tsx` | ponto de entrada, Error Boundary raiz |
| `App.tsx` | sessão, rotas com carregamento tardio, navegação |
| `estilos.css` | **todo** o CSS, em tokens no `:root` |
| `lib/api.ts` | cliente da API, tipos, `ErroApi`, cancelamento |
| `lib/supabase.ts` | SDK sob demanda, upload e URL assinada |
| `components/CartaoLook.tsx` | o cartão de um look |
| `components/Estados.tsx` | carregando, erro, orientação, vazio |
| `components/LimiteDeErro.tsx` | Error Boundary |
| `pages/Recomendar.tsx` | **a tela principal** |
| `pages/GuardaRoupa.tsx` | lista, filtro, disponibilidade, remoção |
| `pages/Cadastro.tsx` | foto → análise → confirmação |
| `pages/Login.tsx` | entrar e criar conta |

### Banco (`supabase/migrations/`)

| Arquivo | Conteúdo |
|---|---|
| `0001_schema.sql` | tabelas, tipos, trigger de novo usuário |
| `0002_rls.sql` | políticas de isolamento por usuário e do bucket |
| `0003_indices_e_seguranca.sql` | índices, restrições, view de métricas corrigida |

Migração é **append-only**: nunca edite um arquivo já aplicado. Crie
`0004_...sql` com o `alter table` que faltou.

---

## 3. Como o fluxo principal funciona

Siga o caminho de `POST /recomendacoes` (`routers/recomendacao.py`):

1. **Valida o evento** contra `DRESS_CODE` em `taxonomia.py`, que define a
   formalidade esperada de 1 a 5.
2. **Carrega o acervo disponível** — antes de gravar qualquer coisa. Gravar o
   contexto primeiro registraria consultas que nunca geraram look, e isso
   distorceria o Hit Rate@3 do RNF04.
3. **Resolve o clima** (`services/clima.py`): com latitude e longitude, consulta
   a Open-Meteo com 4 s de timeout e cache de 10 minutos por célula de ~1 km. Se
   falhar, segue com o que o usuário informou à mão.
4. **Filtros rígidos** (`passa_filtros`): disponibilidade, faixa de temperatura
   com 3 °C de tolerância, calçado fechado se chover, formalidade a no máximo 1
   ponto do alvo. *Filtro rígido elimina o inviável, nunca o "feio" — gosto é
   assunto do score.*
5. **Corte por papel** (`_melhores_do_papel`): mantém as 12 peças mais ajustadas
   ao contexto em cada papel e só então faz o produto cartesiano. Com 200 peças
   isso reduz de ~19 mil candidatos para 1.728.
6. **Score** (`Avaliador.pontuar`): cinco critérios ponderados — ocasião (com
   penalidade por dispersão: blazer com chinelo tem média aceitável e dispersão
   alta), clima, harmonia de cor, estilo aprendido, variedade.
7. **Diversifica**: no máximo uma peça repetida entre os três looks. Três
   variações da mesma camiseta valeriam por uma no Hit Rate@3.
8. **Explica** (`services/explicacao.py`) por template — determinístico e
   gratuito, como o RNF14 exige.
9. **Persiste** contexto e looks em dois inserts em lote e devolve tudo com o
   identificador que o feedback vai usar.

Nada nesse caminho produz 500. Acervo vazio, nenhuma combinação viável e peça
com dados inconsistentes viram 409 ou 422 com mensagem em português que explica
*por quê*, inclusive a temperatura e a formalidade consideradas.

---

## 4. Receitas: quero mudar X, edito o quê

| Quero… | Edite | Depois |
|---|---|---|
| adicionar uma categoria de roupa | `services/taxonomia.py`, tupla `CATEGORIAS` | nada; a API e o seletor da interface leem dela |
| mudar a formalidade de uma peça | mesma tupla, campo `formalidade` | rode `pytest tests/test_recomendador.py` |
| mudar a faixa de temperatura | mesma tupla, `temp_min`/`temp_max` | idem |
| adicionar um tipo de compromisso | `DRESS_CODE` em `taxonomia.py` | aparece sozinho no seletor |
| mudar o peso de um critério | `PESOS_PADRAO` em `recomendador.py` | são renormalizados; a soma não precisa dar 1 |
| adicionar um critério de score | `Avaliador.preparar` e `Avaliador.pontuar` | acrescente a chave em `PESOS_PADRAO` e o rótulo em `NOME_DO_CRITERIO` (`CartaoLook.tsx`) |
| mudar quando exige agasalho | `LIMIAR_SOBREPOSICAO` em `recomendador.py` | |
| mudar a folga de formalidade | `FOLGA_FORMALIDADE` | cuidado: aumentar demais mistura esportivo com social |
| declarar duas cores incompatíveis | `PARES_QUE_DESTOAM` em `services/cor.py` | escreva o teste junto |
| mudar o texto da explicação | `services/explicacao.py`, `por_template` | |
| mudar cores, espaçamento, fontes | tokens no `:root` de `estilos.css` | nunca defina cor fora dos tokens |
| adicionar campo na peça | `schemas.py` → `repositorio.py` (as duas implementações) → migração nova → `api.ts` | os dois repositórios têm de concordar |
| adicionar uma rota | `routers/*.py` + schema de entrada e saída | `response_model` é obrigatório |
| mudar mensagem de erro do Pydantic | `TRADUCOES` em `erros.py` | |

**Regra dos dois repositórios:** toda mudança em `repositorio.py` precisa ser
feita em `RepositorioSupabase` **e** em `RepositorioMemoria`. Se divergirem, a
demonstração passa e a produção quebra — ou o contrário, que é pior porque
ninguém percebe. `tests/test_repositorio_supabase.py` tem um teste que compara a
forma das respostas dos dois; imite-o.

---

## 5. Divisão por integrante

Cada pessoa é **dona** dos seus arquivos: revisa PR de quem mexer neles e
responde por eles na apresentação. Não significa que ninguém mais pode editar.

### Auiri Brito — Scrum Master e infraestrutura

**Arquivos:** `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`,
`frontend/nginx.conf`, `supabase/migrations/`, `.env.example`, `README.md`

**Primeiras tarefas**

1. Criar o projeto no Supabase e aplicar as três migrações. Guardar as chaves e
   distribuir ao time por canal privado — nunca no repositório.
2. Rodar `docker compose up --build` e corrigir o que aparecer (é a primeira
   execução real das imagens).
3. Colocar a aplicação no ar em endereço público. **Isso é pré-requisito do
   RNF04**: teste com 10 usuários reais não acontece em `localhost`.
4. Integração contínua rodando `pytest` a cada push.
5. Confirmar no painel do Supabase que a RLS está ativa nas sete tabelas.

**O que você precisa saber:** a API escolhe entre Supabase e memória em
`config.py:modo_demo`. Se subir em produção e o log disser "MODO DEMONSTRACAO",
falta variável de ambiente — e a autenticação está desligada.

### Bruno Fernando Pereira Costa — back-end

**Arquivos:** `backend/app/routers/`, `repositorio.py`, `schemas.py`, `erros.py`,
`db.py`, `auth.py`

**Primeiras tarefas**

1. Ler `repositorio.py` de ponta a ponta. É a peça central da arquitetura.
2. Exercitar `/docs` e conferir que cada rota tem `response_model`.
3. Implementar a rota que falta: histórico de looks recomendados
   (`GET /looks?limite=20`), que a tela de métricas vai consumir.
4. Manter `RepositorioSupabase` e `RepositorioMemoria` em pé de igualdade.

**O que você precisa saber:** o backend usa a chave **anônima** e repassa o JWT
do usuário, então a RLS vale dentro da API — um bug de lógica vira erro de
permissão, não vazamento. Nunca troque para a service-role key. E use
`_cliente_para_token`: o cliente compartilhado com `postgrest.auth()` por
mutação era o defeito mais grave que a auditoria encontrou (`tests/test_isolamento.py`
explica).

### Lucas Abbade Golveia Sebastião — front-end

**Arquivos:** `frontend/src/pages/`, `App.tsx`, `lib/api.ts`, `lib/supabase.ts`

**Primeiras tarefas**

1. Rodar `npm run dev` e percorrer as quatro telas.
2. Construir a tela de métricas consumindo `GET /metricas` (Hit Rate@3 e
   Precision@3 do RNF04). É o que o time vai mostrar na apresentação.
3. Testar no celular de verdade, incluindo instalar como PWA.
4. Conferir que nenhum `useEffect` que faz requisição fica sem
   `AbortController` — o padrão está em `Recomendar.tsx`.

**O que você precisa saber:** `ErroApi.ehConflito` (409) é situação do
guarda-roupa do usuário e pede orientação; 5xx e falha de rede pedem "tentar de
novo". São painéis diferentes de propósito (`components/Estados.tsx`). E o SDK
do Supabase entra por import dinâmico: não volte a importá-lo estaticamente, ou
o carregamento inicial dobra.

### Lucas Belmonte Alves — visão computacional e recomendação

**Arquivos:** `services/visao.py`, `services/recomendador.py`, `services/cor.py`,
`services/taxonomia.py`, `tests/test_recomendador.py`, `tests/test_cor.py`

**Primeiras tarefas**

1. Instalar `requirements-visao.txt` e confirmar que `/saude` mostra
   `visao_disponivel: true`.
2. **Medir a acurácia com fotos reais de vocês.** Fotografe 40 peças do próprio
   guarda-roupa, anote a categoria correta, rode `/pecas/analisar` e monte uma
   planilha de acerto por categoria. É o dado que o RNF03 exige e que ninguém
   mais pode produzir.
3. Ajustar os `prompts` das categorias em `taxonomia.py` conforme a medição.
   Prompt melhor é mais barato que qualquer outra mudança.
4. Calibrar as faixas de temperatura com o clima real da sua cidade.
5. Levar os pares que destoam (`PARES_QUE_DESTOAM` em `cor.py`) ao consultor de
   imagem para validação, e escrever teste para cada regra que ele confirmar.

**O que você precisa saber:** trocar uma categoria é editar um dicionário — não
há retreino. Todo ajuste de regra precisa de teste; é o que permite responder
"por que este look e não aquele" na banca com o código na tela.

### Sofia Elluf de Mendonça Chagas — design e front-end

**Arquivos:** `frontend/src/estilos.css`, `components/CartaoLook.tsx`,
`components/Estados.tsx`, textos da interface

**Primeiras tarefas**

1. Revisar os tokens do `:root` e fechar a paleta definitiva, clara e escura.
2. Auditar acessibilidade: contraste de cada par texto/fundo (WCAG 2.1 AA),
   alvos de toque de 44 px, e **o nome da cor sempre em texto ao lado da
   amostra** — é o RNF05, e o usuário com daltonismo depende dele.
3. Revisar o texto de todos os estados vazios e de erro. Cada mensagem precisa
   dizer o que aconteceu e o que fazer.
4. Desenhar a tela de métricas junto com o Lucas Abbade.

**O que você precisa saber:** nenhuma cor é definida fora dos tokens do `:root`,
e o bloco escuro só **redefine** tokens — nunca cria cor nova. Esqueleto de
carregamento usa classe própria (`esqueleto-look`, `esqueleto-peca`) e
`aria-hidden`: nunca a mesma classe do componente real.

---

## 6. O que atualizar no Documento de Visão

O documento aprovado descreve um sistema diferente do que foi construído em três
pontos. Divergência entre texto e código é o achado mais fácil de a banca fazer.
**Cada item tem um dono.**

| Seção | O que está escrito | O que foi feito | Dono |
|---|---|---|---|
| **1.2 Escopo, M1** | "treinamento por ajuste fino de modelos pré-treinados" | classificação zero-shot, sem treino | Lucas Belmonte |
| **1.2 Escopo, M7** | infraestrutura própria | Supabase para banco, auth e storage | Auiri |
| **5.1 Figura 1** | fila de tarefas, Postgres e object storage próprios | PWA → FastAPI → Supabase | Auiri |
| **5.2** | Celery, Redis, MinIO | Supabase, rembg, ONNX Runtime, FashionCLIP | Auiri |
| **RNF03** | ≥90% categoria, ≥85% cor | **medir antes de decidir** | Lucas Belmonte |
| **1.4 Referências** | DeepFashion2, YOLO | acrescentar FashionCLIP, rembg, Supabase | Lucas Belmonte |
| **Histórico e capa** | versão 1.1 | nova linha e versão | Auiri |

Redação sugerida para o M1:

> M1, curadoria da taxonomia e avaliação do modelo de visão: definição das
> categorias e dos descritores textuais usados na classificação zero-shot,
> montagem do conjunto de avaliação a partir de fotografias reais dos usuários,
> medição de acurácia por categoria e versionamento dos descritores.

**Sobre o RNF03, o mais importante:** não ajuste a meta antes de medir.
Zero-shot com 24 categorias provavelmente fica abaixo de 90%. Meça na semana 2 e
corrija a meta **com o número na mão**, registrando o tamanho do conjunto de
teste e o número de classes. Meta corrigida com dado é honestidade científica;
meta não atingida sem explicação é falha.

E a defesa do zero-shot é legítima, se dita assim: adicionar uma categoria nova
é editar um dicionário, sem rotular uma única imagem. Para um catálogo de
vestuário que muda, é vantagem de projeto — não só atalho de cronograma.

---

## 7. Regras de trabalho

**Antes de abrir PR**

```bash
cd backend  && python -m pytest        # tem de passar inteiro
cd frontend && npx tsc --noEmit        # tem de sair sem nada
cd frontend && npm run build           # tem de construir
```

**Sempre**

- Teste junto com a mudança de regra. Sem teste, a regra é opinião.
- Mensagem de erro em português, dizendo o que fazer.
- `response_model` em toda rota nova.
- Migração nova, nunca editar uma já aplicada.
- Nenhuma chave no repositório. `.env` está no `.gitignore` — confira antes do
  commit.

**Nunca**

- Trocar a chave anônima do Supabase pela service-role no backend.
- Importar `@supabase/supabase-js` estaticamente no frontend.
- Definir cor fora dos tokens do `:root`.
- Deixar um `useEffect` com requisição sem `AbortController`.
- Usar a mesma classe CSS num esqueleto e no componente real.

**Onde procurar quando algo quebra**

| Sintoma | Onde olhar |
|---|---|
| tela branca | console do navegador; o Error Boundary devia ter contido — veja `LimiteDeErro` |
| "não foi possível falar com a API" | a API está rodando? é a porta 8000? `ORIGENS_PERMITIDAS` inclui a origem do frontend? |
| 500 na API | o log tem o `requisicao=<id>` que a resposta devolveu; procure por ele |
| recomendação sempre igual | `usos_recentes` depende de looks gravados; em memória zera ao reiniciar |
| peça cadastrada nunca aparece | `temp_min`/`temp_max` ou `formalidade` a excluem de todo filtro |
| login não aparece | falta `VITE_SUPABASE_URL` em `frontend/.env.local` |
| métricas mostram número de outro usuário | a migração 0003 não foi aplicada |
