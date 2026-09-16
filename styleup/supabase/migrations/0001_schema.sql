-- StyleUp — esquema inicial
-- Executar no SQL Editor do Supabase, ou via `supabase db push`.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------- perfis
create table if not exists public.perfis (
  id          uuid primary key references auth.users (id) on delete cascade,
  nome        text,
  criado_em   timestamptz not null default now()
);

-- cria o perfil automaticamente a cada novo usuário do Supabase Auth
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.perfis (id, nome)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'nome', split_part(new.email, '@', 1)));
  insert into public.preferencias (usuario_id) values (new.id);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------- peças
-- Papel da peça em um look. A sobreposição (casaco, jaqueta) é opcional.
do $$ begin
  create type papel_peca as enum ('superior', 'inferior', 'calcado', 'sobreposicao');
exception when duplicate_object then null; end $$;

create table if not exists public.pecas (
  id            uuid primary key default gen_random_uuid(),
  usuario_id    uuid not null references auth.users (id) on delete cascade,
  codigo        text not null,                       -- CLO-000001, legível pelo usuário
  papel         papel_peca not null,
  categoria     text not null,                       -- camiseta, calca-jeans, tenis...
  atributos     jsonb not null default '{}'::jsonb,  -- manga, estampa, caimento
  cor_nome      text not null,
  cor_hex       text not null,
  cor_hsv       real[] not null,                     -- [h 0-360, s 0-1, v 0-1]
  neutra        boolean not null default false,
  formalidade   smallint not null check (formalidade between 1 and 5),
  temp_min      real not null default 0,             -- faixa de conforto em °C
  temp_max      real not null default 45,
  resiste_chuva boolean not null default true,
  disponivel    boolean not null default true,
  imagem_path   text,                                -- caminho no bucket 'pecas'
  confianca     jsonb not null default '{}'::jsonb,  -- scores do modelo, para auditoria
  revisada      boolean not null default false,      -- usuário confirmou os atributos
  criado_em     timestamptz not null default now(),
  unique (usuario_id, codigo)
);

create index if not exists pecas_usuario_idx on public.pecas (usuario_id, papel, disponivel);

-- gera CLO-000001 por usuário
create or replace function public.proximo_codigo_peca(p_usuario uuid)
returns text language sql stable as $$
  select 'CLO-' || lpad((count(*) + 1)::text, 6, '0')
  from public.pecas where usuario_id = p_usuario;
$$;

-- ---------------------------------------------------------------- contexto
create table if not exists public.contextos (
  id                uuid primary key default gen_random_uuid(),
  usuario_id        uuid not null references auth.users (id) on delete cascade,
  evento            text not null,                  -- trabalho, casual, academia, formal
  formalidade_alvo  smallint not null check (formalidade_alvo between 1 and 5),
  temperatura       real,
  sensacao          real,
  chuva_prob        real,
  latitude          real,
  longitude         real,
  criado_em         timestamptz not null default now()
);

create index if not exists contextos_usuario_idx on public.contextos (usuario_id, criado_em desc);

-- ---------------------------------------------------------------- looks
create table if not exists public.looks (
  id           uuid primary key default gen_random_uuid(),
  usuario_id   uuid not null references auth.users (id) on delete cascade,
  contexto_id  uuid not null references public.contextos (id) on delete cascade,
  posicao      smallint not null,                   -- 1, 2 ou 3
  score        real not null,
  parcelas     jsonb not null default '{}'::jsonb,  -- score aberto por critério
  explicacao   text,
  criado_em    timestamptz not null default now()
);

create table if not exists public.look_pecas (
  look_id  uuid not null references public.looks (id) on delete cascade,
  peca_id  uuid not null references public.pecas (id) on delete cascade,
  papel    papel_peca not null,
  primary key (look_id, peca_id)
);

create index if not exists looks_usuario_idx on public.looks (usuario_id, criado_em desc);

-- ---------------------------------------------------------------- feedback
create table if not exists public.feedback (
  id          uuid primary key default gen_random_uuid(),
  usuario_id  uuid not null references auth.users (id) on delete cascade,
  look_id     uuid not null references public.looks (id) on delete cascade,
  aprovado    boolean not null,
  criado_em   timestamptz not null default now(),
  unique (usuario_id, look_id)
);

-- ---------------------------------------------------------- personalização
-- Pesos do score por usuário. Começam iguais ao padrão e são ajustados pelo M6.
create table if not exists public.preferencias (
  usuario_id  uuid primary key references auth.users (id) on delete cascade,
  pesos       jsonb not null default
              '{"ocasiao":0.30,"clima":0.25,"cor":0.20,"estilo":0.15,"variedade":0.10}'::jsonb,
  atualizado  timestamptz not null default now()
);

-- --------------------------------------------------- métricas de avaliação
-- Alimenta o RNF04 (Hit Rate@3 e Precision@3) sem consulta manual ao banco.
create or replace view public.metricas_recomendacao as
select
  count(distinct c.id)                                          as consultas,
  count(distinct f.look_id) filter (where f.aprovado)            as looks_aprovados,
  count(distinct c.id) filter (
    where exists (select 1 from public.feedback f2
                   join public.looks l2 on l2.id = f2.look_id
                  where l2.contexto_id = c.id and f2.aprovado)
  )::real / nullif(count(distinct c.id), 0)                      as hit_rate_3,
  count(*) filter (where f.aprovado)::real
    / nullif(count(f.id), 0)                                     as precision_3
from public.contextos c
left join public.looks l  on l.contexto_id = c.id
left join public.feedback f on f.look_id = l.id;
