-- Desfaz 0003. Executar por último (depois de reverter 0005 e 0004).
-- PERDA DE DADOS: todos os registros de consentimento são apagados.
-- LIMITE: latitude e longitude voltam a existir, mas VAZIAS — as coordenadas
-- antigas foram eliminadas de propósito e não há como restaurá-las.
drop function if exists public.excluir_minha_conta();
drop function if exists public.revogar_consentimento();
drop table if exists public.consentimentos;
alter table public.contextos
  add column if not exists latitude  real,
  add column if not exists longitude real;
