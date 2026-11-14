-- StyleUp — looks salvos, estilo no contexto, acessórios e gravação atômica
--
-- IMPACTO NOS DADOS EXISTENTES
--   * Só acrescenta colunas (com valor padrão), um valor ao enum de papel,
--     índices e funções. Nenhuma linha existente é alterada.
--   * ATENÇÃO: um valor de enum não pode ser removido depois (ver reverter/).
--
-- Executar depois de 0004. Pode ser executada mais de uma vez.

-- ------------------------------------------------------------ 1. acessórios
-- Boné, cinto, relógio... Peças opcionais do look. O valor novo só é usado por
-- inserções futuras, então pode ser criado na mesma execução que as funções.
alter type public.papel_peca add value if not exists 'acessorio';

-- ------------------------------------------------- 2. colunas novas
alter table public.looks
  add column if not exists salvo   boolean not null default false,
  add column if not exists titulo  text,
  add column if not exists resumo  text;

alter table public.contextos
  add column if not exists estilo text;

create index if not exists looks_salvos_idx
  on public.looks (usuario_id, criado_em desc) where salvo;
create index if not exists feedback_usuario_idx
  on public.feedback (usuario_id, criado_em desc);
create index if not exists look_pecas_peca_idx
  on public.look_pecas (peca_id);
create index if not exists looks_contexto_idx
  on public.looks (contexto_id);

-- ------------------------------- 3. gravação atômica da recomendação
-- Defeito corrigido: o contexto era gravado antes das validações e os looks um
-- a um, sem transação. Uma falha no meio deixava um contexto órfão, que entrava
-- em "consultas" e distorcia o Hit Rate@3. Uma chamada de função é uma
-- transação: ou entra tudo, ou não entra nada. E são 1 ida ao banco, não 7.
--
-- "security invoker": roda como o usuário, então a RLS confere cada linha.
create or replace function public.registrar_recomendacao(p_contexto jsonb, p_looks jsonb)
returns uuid
language plpgsql
security invoker set search_path = ''
as $$
declare
  v_uid       uuid := auth.uid();
  v_contexto  uuid := (p_contexto ->> 'id')::uuid;
begin
  if v_uid is null then
    raise exception 'não autenticado' using errcode = '42501';
  end if;

  -- a chave estrangeira não passa pela RLS: sem esta checagem, um look poderia
  -- apontar para a peça de outro usuário
  if exists (
    select 1
      from jsonb_array_elements(p_looks) as l,
           jsonb_array_elements(l -> 'pecas') as v
     where not exists (select 1 from public.pecas p
                        where p.id = (v ->> 'peca_id')::uuid and p.usuario_id = v_uid)
  ) then
    raise exception 'peça inexistente ou de outro usuário' using errcode = '42501';
  end if;

  insert into public.contextos
    (id, usuario_id, evento, estilo, formalidade_alvo, temperatura, sensacao, chuva_prob)
  values
    (v_contexto, v_uid, p_contexto ->> 'evento', p_contexto ->> 'estilo',
     (p_contexto ->> 'formalidade_alvo')::smallint,
     (p_contexto ->> 'temperatura')::real,
     (p_contexto ->> 'sensacao')::real,
     (p_contexto ->> 'chuva_prob')::real);

  insert into public.looks
    (id, usuario_id, contexto_id, posicao, score, parcelas, titulo, resumo, explicacao)
  select (l ->> 'id')::uuid, v_uid, v_contexto, (l ->> 'posicao')::smallint,
         (l ->> 'score')::real, coalesce(l -> 'parcelas', '{}'::jsonb),
         l ->> 'titulo', l ->> 'resumo', l ->> 'explicacao'
    from jsonb_array_elements(p_looks) as l;

  insert into public.look_pecas (look_id, peca_id, papel)
  select (l ->> 'id')::uuid, (v ->> 'peca_id')::uuid, (v ->> 'papel')::public.papel_peca
    from jsonb_array_elements(p_looks) as l,
         jsonb_array_elements(l -> 'pecas') as v;

  return v_contexto;
end;
$$;

-- ------------------------------------- 4. leituras agregadas no banco
-- Em quantos dos últimos N looks cada peça apareceu (nota de variedade).
create or replace function public.usos_recentes(p_janela integer default 10)
returns table (peca_id uuid, usos integer)
language sql
stable
security invoker set search_path = ''
as $$
  select lp.peca_id, count(*)::integer
    from public.look_pecas lp
    join (select id from public.looks
           where usuario_id = (select auth.uid())
           order by criado_em desc, posicao
           limit greatest(p_janela, 0)) recentes on recentes.id = lp.look_id
   group by lp.peca_id;
$$;

-- Aprovações por categoria nos últimos N feedbacks (nota de estilo).
-- Defeito corrigido: a API lia TODO o histórico e mandava todos os IDs de look
-- na URL ("in.(...)"); com o uso, a URL passava do limite e a recomendação caía.
create or replace function public.aprovacao_por_categoria(p_limite integer default 200)
returns table (categoria text, aprovados integer, total integer)
language sql
stable
security invoker set search_path = ''
as $$
  select p.categoria,
         (count(*) filter (where f.aprovado))::integer,
         count(*)::integer
    from (select look_id, aprovado from public.feedback
           where usuario_id = (select auth.uid())
           order by criado_em desc
           limit greatest(p_limite, 0)) f
    join public.look_pecas lp on lp.look_id = f.look_id
    join public.pecas p on p.id = lp.peca_id
   group by p.categoria;
$$;

revoke all on function public.registrar_recomendacao(jsonb, jsonb) from public, anon;
revoke all on function public.usos_recentes(integer) from public, anon;
revoke all on function public.aprovacao_por_categoria(integer) from public, anon;
grant execute on function public.registrar_recomendacao(jsonb, jsonb) to authenticated;
grant execute on function public.usos_recentes(integer) to authenticated;
grant execute on function public.aprovacao_por_categoria(integer) to authenticated;
