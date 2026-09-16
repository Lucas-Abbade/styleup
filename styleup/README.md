# StyleUp

Guarda-roupa digital catalogado por foto, com recomendação de looks conforme
clima e ocasião. Implementa os módulos M2 a M7 do Documento de Visão.

**Roda em dois minutos, sem cadastro em nada.** Sem credenciais do Supabase a
API sobe em *modo demonstração*: dados em memória e um guarda-roupa de exemplo
já carregado, com o fluxo completo funcionando. Quando as credenciais aparecem no
`.env`, a mesma API passa a usar Supabase, Postgres e RLS sem trocar uma linha de
código das rotas.

---

## Como rodar (modo demonstração, sem configurar nada)

Precisa de Python 3.11+ e Node 18+.

**Terminal 1 — API**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # leve, ~30 s

uvicorn app.main:app --reload --port 8000
```

O log confirma o modo:

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

Abra <http://localhost:5173>, escolha um compromisso e clique em **Recomendar**.

- Documentação interativa da API: <http://localhost:8000/docs>
- Estado da API: <http://localhost:8000/saude>
- No celular, na mesma rede: `npm run dev -- --host` e acesse o IP da máquina

**Docker (a pilha inteira)**

```bash
docker compose up --build
# frontend em http://localhost:8080 · API em http://localhost:8000/docs
```

**Testes**

```bash
cd backend && python -m pytest                  # 180 testes, ~1 s, sem rede
cd backend && python -m pytest --cov=app        # cobertura: 90%
```

### Habilitando a análise de foto (opcional, ~2 GB)

Sem estas dependências o cadastro por foto continua funcionando: a **cor é medida
de verdade** na imagem (k-means sobre a máscara, só numpy) e a categoria vem como
palpite para você confirmar na tela — a resposta traz `modelo_disponivel: false` e
a interface avisa. Para ligar o modelo:

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu   # ~200 MB
pip install -r requirements-visao.txt
```

### Ligando o Supabase (produção)

1. Crie um projeto em <https://supabase.com> (plano gratuito basta).
2. SQL Editor → execute `supabase/migrations/0001_schema.sql`.
3. SQL Editor → execute `supabase/migrations/0002_rls.sql` e depois
   `supabase/migrations/0003_indices_e_seguranca.sql`.
4. Project Settings → API: copie **URL**, **anon key** e **JWT Secret**.
5. `cp .env.example .env` e preencha; em `frontend/`, `cp .env.example .env.local`.

O bucket `pecas` é criado pela migração 0002, já privado e com políticas de pasta
por usuário. Reinicie a API: o log passa a dizer `conectada ao Supabase`, o login
aparece no frontend e a faixa de demonstração desaparece.

Para desenvolver o frontend sem sujar os dados reais, `MODO_DEMO=true` no `.env`
força a memória mesmo com o Supabase configurado.

---

## Arquitetura

```
Navegador (PWA)                 Backend (FastAPI)              Persistência
─────────────────               ─────────────────              ─────────────────
React + TypeScript ──JWT──▶     routers/pecas.py               Repositorio
Recomendar                      routers/recomendacao.py     ┌── Supabase (produção)
GuardaRoupa                     routers/feedback.py         └── Memória (demo)
Cadastro                                │
      │                                 ├── recomendador.py  filtros, score, rank
      └── upload direto ─────────▶      ├── cor.py           k-means, harmonia
          bucket 'pecas'                ├── taxonomia.py     regras de vestuário
                                        ├── explicacao.py    texto do look
                                        ├── visao.py         rembg + FashionCLIP
                                        └── clima.py         Open-Meteo
```

O ponto central do desenho é a interface `Repositorio` (`app/repositorio.py`).
As rotas não conhecem Supabase: recebem um repositório já **escopado ao usuário**,
sem nenhum método que aceite `usuario_id`. Não existe caminho de código capaz de
ler os dados de outra pessoa por descuido, e a mesma rota é testável sem rede.

Em produção o backend usa a chave **anônima** e repassa o JWT do usuário ao
PostgREST, então as políticas de RLS continuam valendo dentro da API: um erro de
lógica numa rota vira erro de permissão no banco, não vazamento de dados. Usar a
service-role key aqui desligaria essa proteção.

### Estrutura

```
backend/
  app/
    main.py            aplicação, CORS e middleware de tempo de resposta
    config.py          ambiente; decide entre demonstração e Supabase
    auth.py            valida o JWT do Supabase (ou libera, em demonstração)
    db.py              escolhe e entrega o repositório da requisição
    repositorio.py     interface + Supabase + memória semeada  ← camada de dados
    erros.py           tratamento global: envelope, tradução, id de requisição
    schemas.py         contratos da API (espelham a seção 6 do documento)
    routers/           pecas · recomendacao · feedback
    services/          recomendador · cor · taxonomia · explicacao · visao · clima
  tests/
    test_recomendador.py       regras do motor, isoladas
    test_cor.py                k-means, nomeação, harmonia, concordância
    test_api.py                fluxo completo por HTTP e casos de erro
    test_erros.py              envelope de erro e validação estrita
    test_isolamento.py         um cliente por sessão (sem token cruzado)
    test_auth.py               validação de JWT, incluindo token forjado
    test_repositorio_supabase.py  consultas montadas para o banco
    test_clima.py              cache e degradação da API externa
    test_desempenho.py         RNF02 com 200 peças
frontend/
  src/pages/         Recomendar · GuardaRoupa · Cadastro · Login
  src/components/    CartaoLook · Estados (carregando, erro, vazio)
  src/lib/           api.ts (cliente + ErroApi) · supabase.ts
supabase/migrations/ esquema e políticas de RLS
docs/
  guia-do-time.md              como rodar, o que editar, quem faz o quê
  atualizar-documento-de-visao.md
```

Dois arquivos concentram a regra de negócio: `taxonomia.py` (o que o sistema sabe
sobre roupa) e `recomendador.py` (como ele decide). Ambos são puros — sem banco,
sem rede — e é por eles que se começa qualquer ajuste de comportamento.

---

## A funcionalidade principal, passo a passo

`POST /recomendacoes` faz, nesta ordem:

1. **Valida o evento** contra o catálogo (`DRESS_CODE`), que define a formalidade
   esperada de 1 a 5.
2. **Carrega o acervo disponível** — antes de gravar qualquer coisa. Gravar o
   contexto primeiro registraria consultas que nunca geraram look, distorcendo o
   Hit Rate@3 do RNF04.
3. **Resolve o clima**: com latitude e longitude, consulta a Open-Meteo (4 s de
   timeout); se falhar, segue com o que o usuário informou à mão.
4. **Filtros rígidos** (`passa_filtros`): disponibilidade, faixa de temperatura
   com 3 °C de tolerância, calçado fechado se chover, formalidade a no máximo
   1 ponto do alvo. Filtro rígido elimina o inviável, nunca o "feio" — gosto é
   assunto do score.
5. **Corta cada papel nas 12 melhores** peças pelo ajuste individual ao contexto,
   e só então faz o produto cartesiano. Com 200 peças isso reduz de ~19 mil
   candidatos para 1.728, e a recomendação sai em ~6 ms.
6. **Pontua** cada candidato em cinco critérios ponderados — ocasião (com
   penalidade por dispersão: blazer com chinelo tem média aceitável e dispersão
   alta), clima, harmonia de cor (esquemas de Itten), estilo aprendido e
   variedade.
7. **Diversifica**: no máximo uma peça repetida entre os três looks. Três
   variações da mesma camiseta valeriam por uma no Hit Rate@3.
8. **Explica** cada look em linguagem natural, por template — determinístico e
   gratuito, como o RNF14 exige.
9. **Persiste** contexto e looks (dois inserts em lote, não seis) e devolve tudo
   com o identificador que o feedback vai usar.

Nada nesse caminho produz 500. Acervo vazio, nenhuma combinação viável e peça com
dados inconsistentes são situações previstas: viram 409 ou 422 com mensagem em
português, e a mensagem explica *por quê* — inclusive a temperatura e a
formalidade consideradas.

### Estados da interface

| Situação | O que aparece |
|---|---|
| Carregando | Esqueleto dos três cartões, com `aria-busy` |
| Guarda-roupa incompleto | Painel âmbar dizendo qual papel falta, com atalho para cadastrar |
| Nenhuma combinação viável (409) | Painel âmbar com o motivo e atalho para o guarda-roupa |
| API fora do ar ou 5xx | Painel vermelho com "Tentar de novo" |
| Geolocalização negada | Campo de temperatura manual, e o resultado diz "clima não considerado" |
| Sucesso | Três cartões com score, peças, explicação e feedback |

---

## Decisões que o time precisa conhecer

**A visão é zero-shot, não treinada.** O Documento de Visão previa ajuste fino de
segmentação sobre o DeepFashion2. A implementação compara a imagem com descrições
textuais das categorias (FashionCLIP). Ganha-se prazo; perde-se a contribuição de
treinamento. `docs/atualizar-documento-de-visao.md` traz a redação sugerida para
as seções afetadas — **atualizem o documento**, porque divergência entre texto e
código é o achado mais fácil de a banca fazer.

**A meta de acurácia precisa ser medida, não assumida.** O RNF03 promete ≥90% em
categoria e ≥85% em cor. Zero-shot com 24 categorias provavelmente fica abaixo.
Meçam com fotos reais de vocês e corrijam a meta com o dado em mãos.

**A infraestrutura ficou menor que o documento descreve.** Não há Celery, Redis
nem MinIO: o Supabase cobre banco, autenticação e armazenamento, e o
processamento de imagem é síncrono. A contrapartida é que a RLS entrega
isolamento por usuário no próprio banco, algo que a stack original só teria com
código de autorização escrito e testado à mão.

**O modo demonstração desliga a autenticação.** É anunciado no log de
inicialização, em `/saude` e numa faixa no topo da interface. Não suba assim em
nenhum ambiente exposto.

---

## Referências técnicas

- [FashionCLIP](https://huggingface.co/patrickjohncyh/fashion-clip) — CLIP ajustado em catálogos de moda
- [rembg](https://github.com/danielgatis/rembg) — remoção de fundo com U²-Net
- [Open-Meteo](https://open-meteo.com/en/docs) — previsão do tempo, sem chave
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security) — isolamento por usuário
- [Documentação Ultralytics](https://docs.ultralytics.com/) — caminho alternativo, se o time voltar a treinar segmentação


---

## Guia do time

`docs/guia-do-time.md` traz o passo a passo de execução, o mapa de cada arquivo,
as receitas de "quero mudar X, edito o quê", a divisão de responsabilidades por
integrante e o que atualizar no Documento de Visão. **Comece por lá.**
