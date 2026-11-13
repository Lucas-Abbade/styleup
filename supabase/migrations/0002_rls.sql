-- StyleUp — Row Level Security
-- Cada usuário enxerga apenas as próprias linhas. Sem isto o RNF11 (LGPD) não fecha.

alter table public.perfis        enable row level security;
alter table public.pecas         enable row level security;
alter table public.contextos     enable row level security;
alter table public.looks         enable row level security;
alter table public.look_pecas    enable row level security;
alter table public.feedback      enable row level security;
alter table public.preferencias  enable row level security;

-- helper: dono da linha
create policy "perfil proprio" on public.perfis
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "pecas proprias" on public.pecas
  for all using (auth.uid() = usuario_id) with check (auth.uid() = usuario_id);

create policy "contextos proprios" on public.contextos
  for all using (auth.uid() = usuario_id) with check (auth.uid() = usuario_id);

create policy "looks proprios" on public.looks
  for all using (auth.uid() = usuario_id) with check (auth.uid() = usuario_id);

create policy "feedback proprio" on public.feedback
  for all using (auth.uid() = usuario_id) with check (auth.uid() = usuario_id);

create policy "preferencias proprias" on public.preferencias
  for all using (auth.uid() = usuario_id) with check (auth.uid() = usuario_id);

-- look_pecas não tem usuario_id: herda do look
create policy "look_pecas proprias" on public.look_pecas
  for all using (
    exists (select 1 from public.looks l
             where l.id = look_id and l.usuario_id = auth.uid())
  ) with check (
    exists (select 1 from public.looks l
             where l.id = look_id and l.usuario_id = auth.uid())
  );

-- ------------------------------------------------------------- storage
-- Bucket privado 'pecas'. Cada usuário só acessa a própria pasta: pecas/<uid>/<arquivo>
insert into storage.buckets (id, name, public)
values ('pecas', 'pecas', false)
on conflict (id) do nothing;

create policy "upload na propria pasta" on storage.objects
  for insert with check (
    bucket_id = 'pecas' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "leitura da propria pasta" on storage.objects
  for select using (
    bucket_id = 'pecas' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "remocao da propria pasta" on storage.objects
  for delete using (
    bucket_id = 'pecas' and (storage.foldername(name))[1] = auth.uid()::text
  );
