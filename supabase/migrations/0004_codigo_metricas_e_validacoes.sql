-- StyleUp — código CLO por contador, métricas por usuário e validação dos pesos
--
-- IMPACTO NOS DADOS EXISTENTES
--   * Os códigos CLO já atribuídos não mudam. O contador de cada usuário começa
--     no MAIOR número já usado, então o próximo código nunca colide.
--   * Linhas de preferencias com pesos inválidos (chave faltando, valor não
--     positivo, soma diferente de 1) voltam ao padrão antes de a restrição entrar.
--   * A view metricas_recomendacao muda de formato: passa a ter uma linha por
--     usuário e novas colunas. Quem a consulta direto no painel precisa ajustar.
--
-- Executar depois de 0003. Pode ser executada mais de uma vez.

-- ------------------------------------------------- 1. contador de códigos
-- Defeito corrigido: proximo_codigo_peca fazia count(*) + 1. Com as peças 1, 2
-- e 3, apagar a 2 fazia o próximo ser CLO-000003, que já existe — e o cadastro
-- falhava no "unique (usuario_id, codigo)". Um contador nunca volta atrás.
create table if not exists public.contador_pecas (
  usuario_id  uuid primary key references auth.users (id) on delete cascade,
  ultimo      integer not null default 0
);

-- RLS ligada e sem política: o cliente não lê nem escreve o contador; só as
-- funções "security definer" abaixo o alcançam.
alter table public.contador_pecas enable row level security;

insert into public.contador_pecas (usuario_id, ultimo)
select usuario_id,
       max(coalesce(nullif(regexp_replace(codigo, '\D', '', 'g'), '')::integer, 0))
  from public.pecas
 group by usuario_id
on conflict (usuario_id) do update
   set ultimo = greatest(public.contador_pecas.ultimo, excluded.ultimo);

-- "insert ... on conflict do update ... returning" é atômico: duas inserções
-- simultâneas do mesmo usuário recebem números diferentes.
create or replace function public.atribuir_codigo_peca()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
declare
  v_numero integer;
begin
  if new.codigo is null or new.codigo = '' then
    insert into public.contador_pecas as c (usuario_id, ultimo)
    values (new.usuario_id, 1)
    on conflict (usuario_id) do update set ultimo = c.ultimo + 1
    returning c.ultimo into v_numero;
    new.codigo := 'CLO-' || lpad(v_numero::text, 6, '0');
  end if;
  return new;
end;
$$;

drop trigger if exists pecas_atribuir_codigo on public.pecas;
create trigger pecas_atribuir_codigo
  before insert on public.pecas
  for each row execute function public.atribuir_codigo_peca();

-- Mantida por compatibilidade com quem ainda chama a RPC antes de inserir.
-- Agora consome um número do contador (por isso deixou de ser "stable").
create or replace function public.proximo_codigo_peca(p_usuario uuid)
returns text
language plpgsql
volatile
security definer set search_path = ''
as $$
declare
  v_numero integer;
begin
  if p_usuario is distinct from auth.uid() then
    raise exception 'usuário diferente do autenticado' using errcode = '42501';
  end if;
  insert into public.contador_pecas as c (usuario_id, ultimo)
  values (p_usuario, 1)
  on conflict (usuario_id) do update set ultimo = c.ultimo + 1
  returning c.ultimo into v_numero;
  return 'CLO-' || lpad(v_numero::text, 6, '0');
end;
$$;

revoke all on function public.proximo_codigo_peca(uuid) from public, anon;
grant execute on function public.proximo_codigo_peca(uuid) to authenticated;

-- ---------------------------------------------- 2. métricas por usuário
-- Dois defeitos corrigidos:
--   * a view rodava com os direitos do dono e ignorava a RLS: qualquer usuário
--     via os números agregados de todos. "security_invoker" faz a RLS valer.
--   * precision_3 era aprovados ÷ feedbacks dados. A definição é
--     aprovados ÷ (3 × consultas): três looks são mostrados por consulta.
--
-- Definições (K = 3):
--   hit_rate_3  = consultas com ≥ 1 look aprovado ÷ consultas avaliadas
--   precision_3 = looks aprovados ÷ (3 × consultas avaliadas)
-- "Avaliada" = recebeu ao menos um feedback. O total bruto fica em "consultas".
drop view if exists public.metricas_recomendacao;
create view public.metricas_recomendacao
with (security_invoker = true) as
with por_consulta as (
  select c.usuario_id,
         c.id,
         count(l.id)                             as mostrados,
         count(f.id)                             as avaliados,
         count(f.id) filter (where f.aprovado)   as aprovados
    from public.contextos c
    left join public.looks l    on l.contexto_id = c.id
    left join public.feedback f on f.look_id = l.id and f.usuario_id = c.usuario_id
   group by c.usuario_id, c.id
)
select usuario_id,
       count(*)::integer                                   as consultas,
       (count(*) filter (where avaliados > 0))::integer    as consultas_avaliadas,
       coalesce(sum(mostrados), 0)::integer                as looks_mostrados,
       coalesce(sum(aprovados), 0)::integer                as looks_aprovados,
       (count(*) filter (where aprovados > 0))::integer    as consultas_com_acerto,
       (count(*) filter (where aprovados > 0))::real
         / nullif(count(*) filter (where avaliados > 0), 0)        as hit_rate_3,
       coalesce(sum(aprovados), 0)::real
         / nullif(3 * count(*) filter (where avaliados > 0), 0)    as precision_3
  from por_consulta
 group by usuario_id;

-- ------------------------------------------------- 3. validação dos pesos
-- Exatamente os cinco critérios, todos numéricos e positivos, somando 1.
create or replace function public.pesos_validos(p jsonb)
returns boolean
language sql
immutable
as $$
  select case
    when jsonb_typeof(p) <> 'object' then false
    when (select count(*) from jsonb_object_keys(p)) <> 5 then false
    when not (p ?& array['ocasiao', 'clima', 'cor', 'estilo', 'variedade']) then false
    when exists (select 1 from jsonb_each(p) as e(k, v)
                  where jsonb_typeof(v) <> 'number') then false
    else (select bool_and((v #>> '{}')::numeric > 0)
                 and abs(sum((v #>> '{}')::numeric) - 1) <= 0.01
            from jsonb_each(p) as e(k, v))
  end;
$$;

update public.preferencias
   set pesos = default
 where not public.pesos_validos(pesos);

alter table public.preferencias
  drop constraint if exists preferencias_pesos_validos;
alter table public.preferencias
  add constraint preferencias_pesos_validos check (public.pesos_validos(pesos));
