-- StyleUp — correções de segurança e índices de desempenho.
-- Executar depois de 0001 e 0002. É idempotente: pode rodar novamente sem dano.

-- ===========================================================================
-- 1. FALHA DE ISOLAMENTO NA VIEW DE MÉTRICAS
-- ===========================================================================
-- Uma view em Postgres executa com os privilégios de quem a criou, não de quem
-- a consulta. `metricas_recomendacao` lê contextos, looks e feedback — todas com
-- RLS ativa — mas, sendo view, ignorava essas políticas: qualquer usuário
-- autenticado que consultasse `/metricas` recebia os números agregados de TODOS
-- os usuários. Além de errado como métrica, é tratamento indevido de dado
-- pessoal de terceiros (RNF11 / LGPD).
--
-- `security_invoker = true` (PostgreSQL 15+, que é o do Supabase) faz a view
-- rodar com os privilégios de quem consulta, e aí a RLS das tabelas-base volta a
-- valer. A cláusula `where usuario_id = auth.uid()` é redundante com a RLS e
-- está aqui de propósito: defesa em profundidade, e deixa a intenção explícita
-- para quem ler o SQL.

drop view if exists public.metricas_recomendacao;

create view public.metricas_recomendacao
with (security_invoker = true) as
with consultas as (
  select c.id
  from public.contextos c
  where c.usuario_id = auth.uid()
),
avaliacoes as (
  select l.contexto_id, f.aprovado
  from public.feedback f
  join public.looks l on l.id = f.look_id
  where f.usuario_id = auth.uid()
)
select
  (select count(*) from consultas)                                  as consultas,
  (select count(*) from avaliacoes where aprovado)                  as looks_aprovados,
  -- Hit Rate@3: proporção de CONSULTAS com ao menos um look aprovado
  (select count(distinct contexto_id) from avaliacoes where aprovado)::real
    / nullif((select count(*) from consultas), 0)                   as hit_rate_3,
  -- Precision@3: proporção de LOOKS aprovados entre os avaliados
  (select count(*) from avaliacoes where aprovado)::real
    / nullif((select count(*) from avaliacoes), 0)                  as precision_3;

comment on view public.metricas_recomendacao is
  'Hit Rate@3 e Precision@3 do usuário autenticado (RNF04). security_invoker '
  'garante que a RLS das tabelas-base seja respeitada.';

-- ===========================================================================
-- 2. ÍNDICES QUE FALTAVAM
-- ===========================================================================
-- `look_pecas` só tinha a chave primária (look_id, peca_id). Duas consultas do
-- caminho quente da recomendação varrem a tabela por falta de índice:

-- usos_recentes(): parte dos últimos looks e busca os vínculos
create index if not exists look_pecas_look_idx
  on public.look_pecas (look_id);

-- taxa_por_categoria(): navega do vínculo para a peça; e a exclusão de uma peça
-- precisa localizar os vínculos dela para a cascata
create index if not exists look_pecas_peca_idx
  on public.look_pecas (peca_id);

-- salvar_looks() insere por contexto, e a view de métricas agrupa por ele
create index if not exists looks_contexto_idx
  on public.looks (contexto_id);

-- taxa_por_categoria() lê os feedbacks recentes do usuário, em ordem de data
create index if not exists feedback_usuario_data_idx
  on public.feedback (usuario_id, criado_em desc);

-- listar_pecas(disponivel=true) é a consulta mais frequente da API. O índice
-- parcial é menor que o completo porque indexa só as peças disponíveis, que é o
-- único filtro que a recomendação usa.
create index if not exists pecas_disponiveis_idx
  on public.pecas (usuario_id, papel)
  where disponivel;

-- ===========================================================================
-- 3. RESTRIÇÕES DE INTEGRIDADE
-- ===========================================================================
-- O backend valida via Pydantic, mas o banco é a última linha: um script de
-- carga ou um acesso direto pelo painel do Supabase não passa pela API.

do $$ begin
  -- cor_hsv precisa ter exatamente [matiz, saturação, valor]
  alter table public.pecas
    add constraint pecas_cor_hsv_tem_tres
    check (array_length(cor_hsv, 1) = 3);
exception when duplicate_object then null; end $$;

do $$ begin
  alter table public.pecas
    add constraint pecas_faixa_termica_coerente
    check (temp_min <= temp_max);
exception when duplicate_object then null; end $$;

do $$ begin
  -- #rrggbb: o valor vai para o atributo style do frontend
  alter table public.pecas
    add constraint pecas_cor_hex_valida
    check (cor_hex ~ '^#[0-9a-fA-F]{6}$');
exception when duplicate_object then null; end $$;

do $$ begin
  alter table public.looks
    add constraint looks_posicao_valida
    check (posicao between 1 and 3);
exception when duplicate_object then null; end $$;

do $$ begin
  alter table public.looks
    add constraint looks_score_normalizado
    check (score >= 0 and score <= 1);
exception when duplicate_object then null; end $$;

-- ===========================================================================
-- 4. FUNÇÃO COM search_path FIXO
-- ===========================================================================
-- `proximo_codigo_peca` é SECURITY INVOKER (padrão), mas sem search_path fixo
-- uma função assim fica sujeita a sequestro de resolução de nomes por um schema
-- no caminho. Fixar é prática recomendada do próprio Supabase.
create or replace function public.proximo_codigo_peca(p_usuario uuid)
returns text
language sql
stable
set search_path = public
as $$
  select 'CLO-' || lpad((count(*) + 1)::text, 6, '0')
  from public.pecas where usuario_id = p_usuario;
$$;
