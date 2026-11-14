-- Desfaz 0004. Executar depois de reverter 0005 e ANTES de reverter 0003.
-- PERDA DE DADOS: o contador de códigos é apagado. Os códigos CLO das peças
-- permanecem, mas o defeito original volta (código repetido após exclusão).
alter table public.preferencias drop constraint if exists preferencias_pesos_validos;
drop function if exists public.pesos_validos(jsonb);

drop view if exists public.metricas_recomendacao;
create view public.metricas_recomendacao as
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

drop trigger if exists pecas_atribuir_codigo on public.pecas;
drop function if exists public.atribuir_codigo_peca();
drop function if exists public.proximo_codigo_peca(uuid);
create function public.proximo_codigo_peca(p_usuario uuid)
returns text language sql stable as $$
  select 'CLO-' || lpad((count(*) + 1)::text, 6, '0')
  from public.pecas where usuario_id = p_usuario;
$$;
drop table if exists public.contador_pecas;
