# StyleUp

Guarda-roupa digital catalogado por foto, com recomendação de looks conforme
clima e ocasião. Implementa os módulos M2 a M7 do Documento de Visão.

**Decisão de arquitetura:** classificação **zero-shot** (sem treinar modelo) e
**Supabase** para autenticação, banco e armazenamento. Isso troca as semanas de
rotulagem e de infraestrutura por dias, o que é o que torna o MVP viável num
prazo de um mês. O que se perde está registrado em *Trade-offs assumidos*, no
fim deste arquivo — leia antes da apresentação, porque a banca vai perguntar.

---

## Arquitetura

```
Navegador (PWA)                    Backend (FastAPI)             Supabase
─────────────────                  ──────────────────            ──────────────
React + TypeScript  ──JWT──────▶   /pecas/analisar               Auth (usuários)
câmera, guarda-roupa               /pecas                        Postgres + RLS
tela de recomendação               /recomendacoes                Storage (fotos)
        │                          /feedback
        └──── upload direto ─────────────────────────────────▶   bucket 'pecas'

                                   rembg (U²-Net)  ── segmentação
                                   FashionCLIP     ── categoria e atributos
                                   k-means HSV     ── cor predominante
                                   Open-Meteo      ── clima
```

A foto vai do navegador direto para o Storage; o backend recebe só os bytes para
análise. Uma imagem a menos trafegando pelo servidor é meio segundo a menos no
orçamento de 5 s do RNF01.

O backend usa a chave **anônima** do Supabase e repassa o JWT do usuário ao
PostgREST. As políticas de RLS continuam valendo dentro da API: um erro de
lógica numa rota vira erro de permissão no banco, não vazamento de dados.

---

## Estrutura

```
backend/
  app/
    main.py            aplicação e middleware de tempo de resposta
    auth.py            validação do JWT do Supabase
    db.py              cliente Supabase por usuário
    schemas.py         contratos da API (espelham a seção 6 do documento)
    routers/
      pecas.py         6.2 catalogação · 6.3 guarda-roupa
      recomendacao.py  6.4 contexto · 6.5 recomendação
      feedback.py      6.6 feedback e personalização
    services/
      taxonomia.py     categorias, formalidade e faixa térmica  ← regra de negócio
      visao.py         pipeline de visão (M1/M2)
      cor.py           k-means, nomeação e harmonia cromática
      recomendador.py  filtros, score e ranqueamento (M5)       ← núcleo, 100% testado
      explicacao.py    texto por template, LLM opcional (M6)
      clima.py         Open-Meteo (M4)
  tests/               47 testes, rodam em 0,2 s sem rede
frontend/
  src/pages/           Login · Cadastro · GuardaRoupa · Recomendar
  src/lib/             cliente Supabase e cliente da API
supabase/migrations/   esquema e políticas de RLS
```

Dois arquivos concentram a regra de negócio: `taxonomia.py` (o que o sistema
sabe sobre roupa) e `recomendador.py` (como ele decide). Ajuste de comportamento
começa por eles, e ambos são puros — sem banco, sem rede, testáveis isoladamente.

---

## Como rodar

### 1. Supabase (uma vez, ~10 min)

1. Crie um projeto em <https://supabase.com> (plano gratuito basta).
2. SQL Editor → cole e execute `supabase/migrations/0001_schema.sql`.
3. SQL Editor → cole e execute `supabase/migrations/0002_rls.sql`.
4. Project Settings → API: copie a **URL**, a **anon key** e o **JWT Secret**.

O bucket `pecas` é criado pela migração 0002, já privado e com as políticas de
pasta por usuário.

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # leve, ~30 s

cp ../.env.example ../.env                          # preencha as chaves
uvicorn app.main:app --reload --port 8000
```

Documentação interativa em <http://localhost:8000/docs>.

Para trabalhar na visão computacional (só quem mexe em M1/M2):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # ~200 MB
pip install -r requirements-visao.txt
```

Sem essas dependências a API sobe normalmente; apenas `/pecas/analisar` falha
quando chamada. Isso é intencional: quatro pessoas não precisam baixar 2 GB.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local                          # mesmas chaves + VITE_API_URL
npm run dev
```

Abra <http://localhost:5173>. Para testar no celular na mesma rede:
`npm run dev -- --host` e acesse o IP da máquina.

### Testes

```bash
cd backend && python -m pytest        # 47 testes
```

### Docker (opcional)

```bash
docker compose up --build            # sobe só a API; o resto está no Supabase
```

---

## Plano de quatro semanas

O ponto de partida é uma fatia vertical funcionando. Nada bloqueia todo mundo
esperando o modelo ficar bom — o pipeline de visão pode devolver resultado ruim
na semana 1 desde que devolva *alguma coisa*.

### Semana 1 — esqueleto de ponta a ponta
| Quem | Entrega |
|---|---|
| Auiri | Projeto Supabase criado, migrações aplicadas, repositório e branches, `.env` distribuído ao time, deploy de teste no ar |
| Bruno | API subindo com `/saude` e `/pecas` funcionando contra o Supabase real |
| Lucas Abbade | Login e listagem do guarda-roupa (mesmo vazio) |
| Lucas Belmonte | `visao.analisar()` rodando local, medindo tempo e acerto em 20 fotos próprias |
| Sofia | Fluxo das quatro telas e ajuste do CSS base |

**Marco:** login funciona e a lista de peças aparece vazia sem erro.

### Semana 2 — catalogação real
| Quem | Entrega |
|---|---|
| Auiri | Storage com URLs assinadas, CI rodando os testes a cada push |
| Bruno | `/pecas/analisar` e `/pecas` integrados ao upload |
| Lucas Abbade | Tela de cadastro com câmera, prévia e confirmação |
| Lucas Belmonte | Prompts da taxonomia ajustados; planilha de acurácia por categoria |
| Sofia | Tela de confirmação e correção manual dos atributos |

**Marco:** dá para fotografar 15 peças e vê-las catalogadas. **Cadastrem o
próprio guarda-roupa nesta semana** — sem acervo real não há como avaliar
recomendação depois.

### Semana 3 — recomendação
| Quem | Entrega |
|---|---|
| Auiri | Deploy estável e acessível pela internet (necessário para o teste com usuários) |
| Bruno | `/recomendacoes` e `/feedback` completos |
| Lucas Abbade | Tela de recomendação com os três looks e os botões de feedback |
| Lucas Belmonte | Calibragem dos pesos e das faixas de temperatura da taxonomia |
| Sofia | Explicação legível e revisão de acessibilidade (contraste, nome da cor) |

**Marco:** o ciclo completo funciona no celular.

### Semana 4 — avaliação e defesa
| Quem | Entrega |
|---|---|
| Todos | Teste com 10 usuários reais, 5 consultas cada = 50 consultas (RNF04) |
| Lucas Belmonte | Relatório de acurácia da visão e de Hit Rate@3 / Precision@3 |
| Bruno + Auiri | Medição dos percentis de tempo (RNF01 e RNF02) a partir do cabeçalho `X-Tempo-ms` |
| Sofia + Lucas Abbade | Correções de usabilidade apontadas no teste |
| Auiri | Apresentação, roteiro de demonstração e plano de contingência |

**Marco:** números reais nas mãos, não estimativas.

> Reserve o dia anterior à apresentação para ensaio. Demonstração ao vivo com
> upload de foto falha em rede de auditório — grave um vídeo de reserva.

---

## Trade-offs assumidos

Estes pontos foram decididos conscientemente. Levá-los explicitados à banca é
mais forte do que ser pego por eles.

**O M1 mudou de natureza.** O Documento de Visão previa treinar por ajuste fino
um modelo de segmentação sobre o DeepFashion2. A abordagem zero-shot não treina
nada: usa o FashionCLIP comparando a imagem com descrições textuais das
categorias. O que se ganha é prazo; o que se perde é a contribuição de
treinamento. **Atualize a seção 1.2 do documento** — deixar o texto prometendo
treino e entregar zero-shot é a inconsistência mais fácil de a banca notar.

A defesa da escolha é legítima e vale ser dita assim: o zero-shot permite
adicionar uma categoria nova editando um dicionário, sem rotular uma única
imagem. Para um catálogo de vestuário que muda, isso é uma vantagem de projeto,
não só um atalho de cronograma.

**A meta de acurácia precisa ser aferida, não assumida.** O documento promete
≥90% em categoria e ≥85% em cor. Zero-shot com 24 categorias provavelmente fica
abaixo disso. Meçam na semana 2, com fotos reais de vocês. Se ficar em 78%,
**ajustem a meta no documento com a medição em mãos** — meta corrigida com dado
é honestidade científica; meta não atingida sem explicação é falha.

**A infraestrutura ficou menor do que o documento descreve.** Não há Celery,
Redis nem MinIO: o Supabase cobre banco, autenticação e armazenamento, e o
processamento é síncrono. Atualize também a seção 5.2. A contrapartida é que a
RLS entrega isolamento por usuário no banco, algo que a stack original só teria
com código de autorização escrito à mão — e testado.

**O processamento síncrono tem limite.** Uma foto por vez, com o usuário
esperando. Serve para o MVP e para a banca. Se a fila do documento voltar a ser
necessária, o ponto de corte é `/pecas/analisar`; o resto não muda.

**Sem sobreposição no acervo, o frio degrada em vez de falhar.** Se o usuário
não tem casaco cadastrado e a temperatura está baixa, o sistema recomenda mesmo
assim, sem a peça. É o comportamento que o RNF07 pede, e está coberto por teste.

---

## Referências técnicas

- [FashionCLIP](https://huggingface.co/patrickjohncyh/fashion-clip) — CLIP ajustado em catálogos de moda
- [rembg](https://github.com/danielgatis/rembg) — remoção de fundo com U²-Net
- [Open-Meteo](https://open-meteo.com/en/docs) — previsão do tempo, sem chave
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security) — isolamento por usuário
- [Documentação Ultralytics](https://docs.ultralytics.com/) — caminho alternativo, caso o time volte a treinar segmentação
