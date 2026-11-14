-- StyleUp — privacidade (LGPD) e exclusão de conta
--
-- IMPACTO NOS DADOS EXISTENTES
--   * contextos.latitude / contextos.longitude são APAGADAS. As coordenadas já
--     gravadas se perdem de propósito: a recomendação só precisa da temperatura,
--     que continua na tabela. Não há como recuperar depois (ver reverter/).
--   * Nenhum usuário existente tem consentimento registrado: no próximo acesso
--     todos verão a tela do termo antes de continuar.
--
-- Executar depois de 0001 e 0002. Pode ser executada mais de uma vez.

-- ------------------------------------------------- 1. fim das coordenadas
alter table public.contextos
  drop column if exists latitude,
  drop column if exists longitude;

-- ------------------------------------------------------ 2. consentimento
-- Uma linha por aceite: quem, quando, qual versão do termo e quais finalidades.
-- É o registro que demonstra o consentimento (LGPD, art. 8º, § 2º).
create table if not exists public.consentimentos (
  id           uuid primary key default gen_random_uuid(),
  usuario_id   uuid not null references auth.users (id) on delete cascade,
  versao       text not null,
  finalidades  jsonb not null default '{}'::jsonb,  -- {"essencial": true, "localizacao": false}
  aceito_em    timestamptz not null default now(),
  revogado_em  timestamptz
);

create index if not exists consentimentos_usuario_idx
  on public.consentimentos (usuario_id, aceito_em desc);

alter table public.consentimentos enable row level security;

drop policy if exists "consentimentos proprios (leitura)" on public.consentimentos;
create policy "consentimentos proprios (leitura)" on public.consentimentos
  for select using (auth.uid() = usuario_id);

drop policy if exists "consentimentos proprios (aceite)" on public.consentimentos;
create policy "consentimentos proprios (aceite)" on public.consentimentos
  for insert with check (auth.uid() = usuario_id and revogado_em is null);

-- Sem política de update/delete: o registro é evidência e não pode ser editado
-- pelo cliente. A revogação passa pela função abaixo, que só carimba a data.
create or replace function public.revogar_consentimento()
returns void
language sql
security definer set search_path = ''
as $$
  update public.consentimentos
     set revogado_em = now()
   where usuario_id = (select auth.uid()) and revogado_em is null;
$$;

revoke all on function public.revogar_consentimento() from public, anon;
grant execute on function public.revogar_consentimento() to authenticated;

-- ---------------------------------------------------- 3. exclusão da conta
-- Remove o usuário de auth.users; o "on delete cascade" de todas as tabelas
-- leva perfil, peças, contextos, looks, feedback, preferências e consentimentos.
--
-- As FOTOS não saem por aqui: o Supabase bloqueia delete direto em
-- storage.objects. O backend apaga a pasta do usuário pela API do Storage
-- ANTES de chamar esta função (ver RepositorioSupabase.excluir_conta).
create or replace function public.excluir_minha_conta()
returns void
language plpgsql
security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'não autenticado' using errcode = '42501';
  end if;
  delete from auth.users where id = v_uid;
end;
$$;

revoke all on function public.excluir_minha_conta() from public, anon;
grant execute on function public.excluir_minha_conta() to authenticated;

-- -------------------------------------- 4. criação de perfil mais robusta
-- "on conflict do nothing": reexecutar o gatilho (ou recriar um usuário com o
-- mesmo id em teste) não pode impedir o cadastro.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.perfis (id, nome)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'nome', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  insert into public.preferencias (usuario_id) values (new.id)
  on conflict (usuario_id) do nothing;
  return new;
end;
$$;
