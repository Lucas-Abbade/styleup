# O que atualizar no Documento de Visão

A implementação seguiu um caminho diferente do que a versão 1.1 do documento
descreve. As mudanças abaixo precisam entrar no texto **antes** da apresentação:
divergência entre documento e código é o achado mais fácil de a banca fazer.

O `docs/guia-do-time.md` traz a mesma lista com **dono por seção**.

## 1.2 Escopo — módulo M1

O texto atual promete "treinamento por ajuste fino de modelos pré-treinados,
avaliação e versionamento dos modelos". A implementação usa classificação
zero-shot, sem treino.

Redação sugerida:

> M1, curadoria da taxonomia e avaliação do modelo de visão: definição das
> categorias e dos descritores textuais usados na classificação zero-shot,
> montagem do conjunto de avaliação a partir de fotografias reais dos usuários,
> medição de acurácia por categoria e versionamento dos descritores.

## 1.2 Escopo — módulo M7

Trocar "contêineres e implantação" próprios pela descrição real: Supabase para
banco, autenticação e armazenamento; FastAPI para a API; nginx servindo o PWA.

## 5.1 Perspectiva do Produto — Figura 1

A figura mostra fila de tarefas, Postgres próprio e object storage próprio.
Redesenhar com três blocos: PWA, API FastAPI e Supabase (Auth, Postgres,
Storage). O processamento de imagem é síncrono; não há Celery nem Redis.

## 5.2 Licença e Instalação

Remover Celery, Redis e MinIO. Acrescentar Supabase, rembg, ONNX Runtime e
FashionCLIP.

## RNF03 — meta de acurácia

Só ajustar **depois** de medir, com fotos reais de vocês. Registrar o número de
categorias avaliadas (24, na taxonomia atual) e o tamanho do conjunto de teste,
sem os quais a meta não é verificável.

Meta corrigida com dado em mãos é honestidade científica; meta não atingida sem
explicação é falha.

## 1.4 Referências

- Remover DeepFashion2 e a documentação do YOLO se o treino não for retomado.
- Acrescentar FashionCLIP, rembg, Open-Meteo e a documentação do Supabase.
- Confirmar a situação do Plano de Implementação: se ainda não existe, é (3).

## Seção 7 — Características Não-Funcionais

Dois requisitos ganharam implementação concreta que vale citar no texto:

- **RNF10 (segurança):** o isolamento por usuário é feito por Row Level Security
  no próprio Postgres, e a API repassa o JWT do usuário em vez de usar chave de
  serviço. Vale uma frase, porque é mais forte do que autorização em código.
- **RNF11 (LGPD):** a exclusão de uma peça remove também a imagem do bucket, e a
  view de métricas respeita a RLS (`security_invoker`).

## Histórico de revisão e capa

Acrescentar a linha desta revisão e ajustar a versão na capa.
