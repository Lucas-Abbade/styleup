-- Desfaz 0005. Executar ANTES de reverter 0004.
-- PERDA DE DADOS: a marca de "look salvo", o título e o resumo dos looks e o
-- estilo dos contextos são apagados.
-- LIMITE: o valor 'acessorio' do enum papel_peca NÃO é removido — o Postgres não
-- remove valor de enum. Peças cadastradas como acessório continuam válidas no
-- banco; a versão antiga da API apenas não as usa nos looks.
drop function if exists public.aprovacao_por_categoria(integer);
drop function if exists public.usos_recentes(integer);
drop function if exists public.registrar_recomendacao(jsonb, jsonb);
drop index if exists public.looks_contexto_idx;
drop index if exists public.look_pecas_peca_idx;
drop index if exists public.feedback_usuario_idx;
drop index if exists public.looks_salvos_idx;
alter table public.contextos drop column if exists estilo;
alter table public.looks
  drop column if exists resumo,
  drop column if exists titulo,
  drop column if exists salvo;
