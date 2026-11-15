# Relatório de melhorias — novembro de 2026

Revisão completa do backend (as cinco fases do roteiro de melhorias), do motor de
looks e do frontend (reimplementado conforme o protótipo). Este documento diz o que
mudou, como cada item foi verificado, o que muda para quem usa a API e o que ficou
para o time.

## 1. Resumo

| Área | Antes | Depois |
|---|---|---|
| Testes do backend | 55 (cor e motor) | 186 (motor, rotas, defeitos, LGPD, visão, clima, auth) |
| Migrações | 2, sem teste | 5, com reversão e teste em Postgres local |
| Idas ao banco por recomendação | 13 | 5 |
| Recomendação com guarda-roupa grande (30×20×10×10) | 344 ms só no motor | 88 ms |
| Erros | 500 com stack trace | `{"erro", "codigo"}` em português |
| Frontend | 4 telas | protótipo completo + perfil, consentimento, exclusão |
| Rodar sem Supabase | não | modo demonstração |

## 2. As cinco fases, item a item

### Fase 1 — Segurança e privacidade

| # | Item | O que foi feito | Verificação |
|---|---|---|---|
| 1 | JWT secret vazado | **Ação do time** (ver §6). `.env` nunca esteve no histórico do git — conferido. O `.env.example` trazia a URL e a chave anon de um projeto real; trocados por marcadores. | `git log --all -- .env` |
| 2 | `print("DEBUG url…")` | Removido. Mensagens de token inválido não descrevem mais a validação por dentro; o motivo vai para o log. | `test_nenhum_print_de_depuracao_no_codigo` |
| 3 | Cliente Supabase global | Um cliente por requisição (`repositorio/supabase.py`), com o JWT em `ClientOptions(headers=…)`: banco **e** Storage autenticados como o usuário. Remoção de foto conferida pelo retorno; o `except: pass` saiu. | `test_banco_e_storage_levam_o_token_do_usuario`, `test_clientes_nao_sao_compartilhados_entre_requisicoes`, `test_remocao_de_foto_e_conferida…` |
| 4 | LGPD | Coordenadas não são mais gravadas (migração 0003) e saem arredondadas (~1 km) para a Open-Meteo. Tabela `consentimentos` com versão, data e finalidades; aceite exigido nas rotas de dados; localização é finalidade opcional, separada. | `test_coordenadas_nunca_sao_gravadas`, `test_perfil.py`, `casos.sql` |
| 5 | Exclusão de conta | `DELETE /perfil`: apaga a pasta inteira do usuário no bucket (com paginação), confere, e só então remove a conta — o `on delete cascade` leva o resto. Também: `GET /perfil/exportar` (cópia dos dados). | `test_excluir_conta…` (API e repositório), `casos.sql` |

### Fase 2 — Lógica e dados

| # | Item | O que foi feito | Verificação |
|---|---|---|---|
| 1 | Código CLO repetido | Contador por usuário, atribuído por gatilho no banco (atômico). O contador começa no maior código já usado. | `casos.sql` (cenário 1-2-3, apaga a 2), `test_codigo_clo_nao_se_repete…` |
| 2 | Cor divergente | Editar a cor recalcula `cor_hsv` e `neutra` a partir do hex; a explicação usa o `cor_nome` do banco. | `test_corrigir_a_cor_recalcula_hsv…`, `test_explicacao_usa_o_nome_de_cor_corrigido` |
| 3 | Feedback sem limite | Agregado no banco (`aprovacao_por_categoria`), limitado aos últimos 200 feedbacks (`JANELA_FEEDBACK`). Nenhum ID vai na URL. | `test_preferencias_por_categoria_nao_mandam_ids_na_url`, `casos.sql` |
| 4 | Divisão por zero | `ajustar_pesos` devolve os pesos intactos quando o look não tem parcelas. | `test_look_sem_parcelas_nao_divide_por_zero` |
| 5 | Contexto órfão | A rota valida tudo primeiro e grava no final, numa única função SQL (uma transação). | `test_guarda_roupa_vazio_nao_deixa_contexto_orfao`, `test_falha_ao_gravar_looks…`, `casos.sql` |
| 6 | Métricas | View por usuário, com `security_invoker` (a antiga ignorava a RLS). Precision@3 = aprovados ÷ (3 × consultas avaliadas). | `test_metricas_seguem_a_definicao`, `casos.sql` |
| 7 | Validação dos pesos | Restrição no banco (`pesos_validos`) e normalização na API; pesos inválidos voltam ao padrão. | `casos.sql`, `test_pesos_corrompidos…` |
| 8 | Validação de entrada | `cor_hsv` (3 valores, faixas), hex, categoria × papel, temperatura. Peça malformada é ignorada na recomendação, com log. | `test_validacao_de_entrada`, `test_peca_malformada_nao_derruba…` |
| 9 | Erros do Supabase | Traduzidos por código: duplicidade (409), sessão (401), permissão (403), rede (503), migração pendente (500 com instrução). | `test_erros_do_supabase_viram_respostas_adequadas` |
| 10 | Texto do frio | Mesmo limiar do motor (18 °C); "pedem agasalho" só quando o look tem agasalho. | `test_texto_do_frio_bate_com_a_regra_do_motor` |
| 11 | Open-Meteo | Probabilidade de chuva pela série horária. **Ver §5:** não foi possível testar ao vivo. | `test_clima.py` (transporte simulado) |

### Fase 3 — Desempenho

| # | Item | O que foi feito |
|---|---|---|
| 1 | `async def` bloqueante | `/pecas/analisar` e `/recomendacoes` são `def` (threadpool). Teste: duas análises simultâneas levam o tempo de uma e o `/saude` responde no meio. |
| 2 | Cache do clima | 15 min por local arredondado; uma conexão HTTP reaproveitada. |
| 3 | Gravação em lote | Uma chamada grava contexto, looks e peças. |
| 4 | Pré-filtro | 12 melhores peças por papel (6 sobreposições), reservando vagas a cores ainda não representadas. |
| 5 | Aquecimento | rembg e FashionCLIP carregam em segundo plano na subida; `/saude` informa o estado. |
| 6 | Medição | `scripts/medir_tempos.py` (§4). |

### Fase 4 — Testes e validação

1. **Acurácia:** `scripts/medir_acuracia.py`, com o formato do CSV em
   `backend/avaliacao/LEIA-ME.md`. Relata categoria, cor, estilo, manga e estampa, com
   intervalo de confiança, top-3, confusões e tempo por foto.
2. **Rotas:** testadas com `TestClient` sobre o repositório em memória; o repositório do
   Supabase é testado contra um cliente simulado.
3. **Concorrência:** `test_desempenho.py` e `test_clientes_nao_sao_compartilhados…`.
4. **Hit Rate@3 / Precision@3:** conferidos com números feitos à mão, na API e no SQL.

### Fase 5 — Organização

1. `repositorio/` separa o acesso a dados das rotas.
2. Corpo de erro único: `{"erro": "...", "codigo": "..."}`.
3. README, `docs/como-rodar.md` e este relatório.
4. `LIMIAR_SOBREPOSICAO` é a única fonte do limiar de frio (motor e explicação).

## 3. Mudanças de comportamento da API

Nada foi removido; o frontend antigo continuaria funcionando, com as exceções marcadas.

| Mudança | Efeito em clientes antigos |
|---|---|
| **Consentimento exigido** nas rotas de peças, recomendação e feedback | **Quebra:** 403 `consentimento_pendente` até o aceite. Desligável com `EXIGIR_CONSENTIMENTO=false`. |
| Corpo de erro `{"erro","codigo","detail"}` | Compatível: `detail` continua vindo, com a mesma mensagem. |
| `POST /recomendacoes`: `evento` passou a ser opcional; aceita `texto`, `estilo`, `inspiracao` | Compatível. |
| Resposta da recomendação ganhou `titulo`, `resumo`, `avisos`, `contexto.entendido` | Compatível (campos novos). |
| Recomendação **degrada em vez de falhar**: sem peça adequada ao clima, afrouxa o filtro daquele papel e explica em `avisos` | Onde vinha 409, agora pode vir 200 com aviso. O 409 fica para papel inexistente. |
| Sobreposição opcional entre 18 e 22 °C e em eventos sociais; acessórios opcionais (papel `acessorio`) | Looks podem ter 3 a 6 peças. |
| `latitude`/`longitude` só são usadas com o consentimento de localização; nunca gravadas | Sem o consentimento, o clima automático não acontece. |
| `PecaEntrada`: `cor_hsv` e `neutra` opcionais (calculados do hex); categoria precisa combinar com o papel | Entrada incoerente passa a dar 422. |
| `DELETE /pecas/{id}` falha (502) se a foto não puder ser apagada | Antes apagava o registro e deixava a foto. |
| `/metricas`: novos campos; Precision@3 com a definição correta | Os valores mudam. |
| `/saude`: novos campos (`modo_demo`, `visao`) | Compatível. |
| Faixas térmicas de calças e camisas alargadas (até 34–38 °C) | Mais opções no calor. |

## 4. Medições

Feitas neste ambiente de desenvolvimento (2 CPUs, sem Supabase e sem os modelos de visão):

| Medida | Antes | Depois |
|---|---|---|
| Motor, guarda-roupa pequeno (8×6×4×3 peças) | 3 ms | 8 ms |
| Motor, médio (15×10×6×4) | 18 ms | 29 ms |
| Motor, grande (30×20×10×10) | 344 ms | 88 ms |
| Idas ao banco por recomendação | 13 | 5 |
| Passadas do codificador de texto por foto | 3 | 0 (feitas uma vez, na subida) |
| Chamadas para assinar URLs de N fotos (front) | N | 1 |
| `POST /recomendacoes` em modo demonstração | — | 3 ms (mediana de 20) |

O motor ficou mais lento em guarda-roupas pequenos porque pontua mais coisas (contraste
de claridade, croma, estilo); o ganho está no teto, que agora é limitado.

**Não medido aqui** (precisa do ambiente real): os 4 s da catalogação, os 2,7 s da
recomendação e os 128 s da primeira requisição. Rode, com a API real no ar:

```bash
python -m scripts.medir_tempos --token <JWT> --foto peca.jpg --latitude -15.6 --longitude -56.1
```

## 5. O que não pôde ser verificado

- **Supabase de verdade.** O código do repositório foi testado contra um cliente
  simulado, e o SQL contra um Postgres 16 local com uma imitação do ambiente do Supabase
  (`auth.uid()`, papéis, RLS). Falta um teste de ponta a ponta num projeto real —
  em especial a exclusão de conta (`delete from auth.users` dentro de função) e o Storage.
- **Modelos de visão.** Este ambiente não alcança o Hugging Face; o FashionCLIP não
  rodou. A lógica em volta dele está testada com vetores sintéticos, mas acurácia e tempo
  reais só saem do `medir_acuracia` na máquina do time.
- **Open-Meteo ao vivo.** A hipótese do roteiro era que `precipitation_probability` não
  existe em `current`. A leitura do código-fonte do servidor indica que existe; não foi
  possível confirmar com uma chamada. A solução adotada (série horária) funciona nos dois
  casos. Um `curl` resolve a dúvida.
- **Definição "do documento" para as métricas.** O Documento de Visão não veio no
  pacote. Foram usadas as definições usuais (§2, fase 2, item 6); confiram com o texto.

## 6. Pendências do time

1. **Trocar o JWT secret** exposto no print (passos em `docs/como-rodar.md`, §4).
2. **Aplicar as migrações 0003–0005** no Supabase, lendo a nota de impacto de cada uma.
3. **Revisar o termo de consentimento** (`backend/app/termo.py`): é um rascunho técnico.
   Preencher controlador e contato; validar com o orientador.
4. **Rotular 50–100 fotos** e rodar `medir_acuracia`.
5. **Medir os tempos** no ambiente real e registrar o "depois".
6. **Atualizar o `supabase-py`**: a versão fixada (2.11.0) não aceita as chaves novas
   (`sb_publishable_…`), e as chaves antigas estão sendo descontinuadas. A partir da 2.16
   aceita; o código usa só `ClientOptions(headers=…)`, que existe nas duas. Não foi
   atualizado aqui porque não havia como testar contra um projeto real.
7. **Fotos do protótipo**: para usar as fotos da splash e do destaque, coloquem os
   arquivos em `frontend/public/img/splash.jpg` e `hero.jpg`. Sem eles aparece a
   ilustração vetorial.
8. **Comunidade**: a aba existe, com uma tela "em breve". Não há backend para ela.

## 7. Decisões tomadas sem consulta

O roteiro pedia para perguntar antes; o pedido desta revisão foi não parar. Os valores
abaixo são fáceis de mudar e estão num lugar só:

| Decisão | Valor | Onde |
|---|---|---|
| Peças por papel no pré-filtro | 12 (6 sobreposições) | `recomendador.TOP_N_POR_PAPEL` |
| Validade do cache do clima | 15 min | `clima.VALIDADE_CACHE` |
| Janela de feedback | 200 | `JANELA_FEEDBACK` |
| Texto e versão do termo | `2026-11-v1` | `termo.py`, `VERSAO_TERMO` |
| Consentimento obrigatório por padrão | sim | `EXIGIR_CONSENTIMENTO` |
| Métricas sobre consultas *avaliadas* | sim | view `metricas_recomendacao` |
| Exclusão de conta por função SQL (sem chave de serviço no backend) | — | migração 0003 |
| Peso da diversidade (MMR) | λ = 0,7 | `recomendador.LAMBDA_DIVERSIDADE` |

Sobre os commits: o roteiro pedia um por item. Como a troca do acesso a dados atravessa
quase todas as rotas, o trabalho ficou em cinco commits por área (motor, banco, API,
frontend, documentação), cada um listando os itens que resolve.

## 8. Além do roteiro

**Motor de looks** — harmonia de cor com contraste de claridade e croma (sem bônus para
complementares, que não tem respaldo empírico); jeans azul como neutro; penalidade para
excesso de cores e de estampas; conforto térmico que não pune a peça dentro da própria
faixa; eventos com peças preferidas e vetadas (academia ≠ em casa); pedido em texto livre
("faculdade, all black, dia frio"); diretrizes de estilo; acessórios; diversidade por MMR;
título e resumo de cada look; avisos quando algo foi flexibilizado.

**Catalogação** — peça sobre fundo branco antes do modelo; média dos prompts por
categoria; recorte sem fundo devolvido à interface (só ele é armazenado); mais nomes de
cor (grafite, verde-oliva, cáqui, caramelo, mostarda, azul-claro); sinal de baixa confiança.

**Frontend** — ver o commit `feat(front)` e as capturas geradas por `e2e/fluxo_demo.py`.
