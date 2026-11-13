# O que atualizar no Documento de Visão

A implementação seguiu um caminho diferente do que a versão 1.1 do documento
descreve. As mudanças abaixo precisam entrar no texto **antes** da apresentação:
divergência entre documento e código é o achado mais fácil de a banca fazer.

## 1.2 Escopo — módulo M1

O texto atual promete "treinamento por ajuste fino de modelos pré-treinados,
avaliação e versionamento dos modelos". A implementação usa classificação
zero-shot, sem treino.

Redação sugerida:

> M1, curadoria da taxonomia e avaliação do modelo de visão: definição das
> categorias e dos descritores textuais usados na classificação zero-shot,
> montagem do conjunto de avaliação a partir de fotografias reais dos usuários,
> medição de acurácia por categoria e versionamento dos descritores.

## 5.2 Licença e Instalação — pilha de tecnologias

Remover Celery, Redis e MinIO. Acrescentar Supabase e as bibliotecas realmente
usadas: rembg, ONNX Runtime, transformers.

## 5.1 Perspectiva do Produto — Figura 1

A figura mostra fila de tarefas, Postgres próprio e object storage próprio.
Redesenhar com três blocos: PWA, API FastAPI e Supabase (Auth, Postgres, Storage).

## RNF03 — meta de acurácia

Só ajustar **depois** de medir, na semana 2, com fotos reais. Registrar o número
de categorias avaliadas (24, na taxonomia atual) e o tamanho do conjunto de
teste, sem os quais a meta não é verificável.

## 1.4 Referências

- Remover DeepFashion2 e a documentação do YOLO se o treino não for retomado.
- Acrescentar FashionCLIP, rembg e a documentação do Supabase.
- Confirmar a situação do Plano de Implementação: se ainda não existe, é (3).

## Histórico de revisão e capa

Acrescentar a linha desta revisão e ajustar a versão na capa.
