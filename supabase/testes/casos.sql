-- Casos de teste das migrações. Cada bloco falha com mensagem clara (ASSERT).
\set ON_ERROR_STOP on
\set QUIET on
\set A '11111111-1111-1111-1111-111111111111'
\set B '22222222-2222-2222-2222-222222222222'
\set L '00000000-0000-0000-0000-0000000000aa'

create or replace function pg_temp.entrar(p uuid) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', p)::text, false);
$$;

insert into auth.users (id, email) values (:'A', 'ana@teste.dev'), (:'B', 'bruno@teste.dev');

-- ---------------------------------------------------------------- legado
do $$ begin
  assert not exists (select 1 from information_schema.columns
                      where table_name = 'contextos' and column_name in ('latitude', 'longitude')),
    'LGPD: contextos ainda tem latitude/longitude';
  assert (select temperatura from public.contextos
           where usuario_id = '00000000-0000-0000-0000-0000000000aa') = 30,
    'a temperatura do contexto antigo deveria ter sido preservada';
  assert (select ultimo from public.contador_pecas
           where usuario_id = '00000000-0000-0000-0000-0000000000aa') = 3,
    'contador deveria começar no maior código já usado (3)';
  assert public.pesos_validos((select pesos from public.preferencias
           where usuario_id = '00000000-0000-0000-0000-0000000000aa')),
    'pesos inválidos do legado deveriam ter voltado ao padrão';
end $$;

-- ------------------------------------------- código CLO depois de exclusão
set role authenticated;
select pg_temp.entrar(:'L');
insert into public.pecas (usuario_id, papel, categoria, cor_nome, cor_hex, cor_hsv, formalidade)
values (:'L', 'inferior', 'calca-jeans', 'azul', '#2f5fb3', '{218,0.74,0.7}', 2);
do $$ begin
  assert (select codigo from public.pecas where categoria = 'calca-jeans') = 'CLO-000004',
    'código após exclusão deveria ser CLO-000004, veio ' ||
    (select codigo from public.pecas where categoria = 'calca-jeans');
end $$;

select pg_temp.entrar(:'A');
insert into public.pecas (usuario_id, papel, categoria, cor_nome, cor_hex, cor_hsv, formalidade)
select :'A', p.papel::public.papel_peca, p.categoria, 'preto', '#000000', '{0,0,0}', 2
  from (values ('superior', 'camiseta'), ('inferior', 'calca-jeans'), ('calcado', 'tenis'),
               ('acessorio', 'bone')) as p(papel, categoria);
delete from public.pecas where codigo = 'CLO-000002';
insert into public.pecas (usuario_id, papel, categoria, cor_nome, cor_hex, cor_hsv, formalidade)
values (:'A', 'inferior', 'calca-sarja', 'bege', '#d9c6a3', '{38,0.25,0.85}', 3);
do $$ begin
  assert (select array_agg(codigo order by codigo) from public.pecas)
         = array['CLO-000001', 'CLO-000003', 'CLO-000004', 'CLO-000005'],
    'códigos de A: ' || (select string_agg(codigo, ',' order by codigo) from public.pecas);
  assert (select count(*) from public.contador_pecas) = 0,
    'o cliente não deveria enxergar o contador';
  assert public.proximo_codigo_peca(auth.uid()) = 'CLO-000006', 'RPC antiga deveria seguir o contador';
end $$;

-- --------------------------------------------------- isolamento por RLS
select pg_temp.entrar(:'B');
do $$ begin
  assert (select count(*) from public.pecas) = 0, 'B enxergou peças de A';
  begin
    perform public.proximo_codigo_peca('11111111-1111-1111-1111-111111111111');
    assert false, 'B conseguiu consumir o contador de A';
  exception when insufficient_privilege then null; end;
end $$;

-- ------------------------------------- gravação atômica da recomendação
select pg_temp.entrar(:'A');
do $$
declare
  sup uuid := (select id from public.pecas where categoria = 'camiseta');
  inf uuid := (select id from public.pecas where categoria = 'calca-sarja');
  cal uuid := (select id from public.pecas where categoria = 'tenis');
  ace uuid := (select id from public.pecas where categoria = 'bone');
  alheia uuid;
  i int;
begin
  for i in 1..3 loop
    perform public.registrar_recomendacao(
      jsonb_build_object('id', ('aaaaaaaa-0000-0000-0000-00000000000' || i)::uuid,
                         'evento', 'casual', 'estilo', 'minimalista',
                         'formalidade_alvo', 2, 'temperatura', 30),
      (select jsonb_agg(jsonb_build_object(
                'id', ('bbbbbbbb-0000-0000-000' || i || '-00000000000' || n)::uuid,
                'posicao', n, 'score', 0.8, 'parcelas', '{"cor": 0.9}'::jsonb,
                'titulo', 'Casual • Neutros', 'resumo', 'r', 'explicacao', 'e',
                'pecas', jsonb_build_array(
                   jsonb_build_object('peca_id', sup, 'papel', 'superior'),
                   jsonb_build_object('peca_id', inf, 'papel', 'inferior'),
                   jsonb_build_object('peca_id', cal, 'papel', 'calcado'),
                   jsonb_build_object('peca_id', ace, 'papel', 'acessorio'))))
         from generate_series(1, 3) n));
  end loop;
  assert (select count(*) from public.contextos) = 3, 'deveriam existir 3 contextos';
  assert (select count(*) from public.looks) = 9, 'deveriam existir 9 looks';
  assert (select count(*) from public.look_pecas) = 36, 'deveriam existir 36 vínculos';

  -- falha no meio (peça de outro usuário): nada pode ficar gravado
  reset role;
  select id into alheia from public.pecas
   where usuario_id = '00000000-0000-0000-0000-0000000000aa' limit 1;
  set role authenticated;
  begin
    perform public.registrar_recomendacao(
      '{"id": "aaaaaaaa-0000-0000-0000-000000000009", "evento": "casual", "formalidade_alvo": 2}'::jsonb,
      jsonb_build_array(jsonb_build_object(
        'id', 'bbbbbbbb-0000-0000-0009-000000000001', 'posicao', 1, 'score', 0.5,
        'pecas', jsonb_build_array(jsonb_build_object('peca_id', alheia, 'papel', 'superior')))));
    assert false, 'recomendação com peça alheia deveria falhar';
  exception when insufficient_privilege then null; end;
  assert (select count(*) from public.contextos) = 3, 'ficou contexto órfão após a falha';
end $$;

-- ------------------------------------------------------------- métricas
-- consulta 1: 1 aprovado + 1 rejeitado · consulta 2: sem feedback · consulta 3: 2 rejeitados
insert into public.feedback (usuario_id, look_id, aprovado) values
  (:'A', 'bbbbbbbb-0000-0000-0001-000000000001', true),
  (:'A', 'bbbbbbbb-0000-0000-0001-000000000002', false),
  (:'A', 'bbbbbbbb-0000-0000-0003-000000000001', false),
  (:'A', 'bbbbbbbb-0000-0000-0003-000000000002', false);
do $$
declare m record;
begin
  select * into m from public.metricas_recomendacao;
  assert (select count(*) from public.metricas_recomendacao) = 1, 'a view deveria ter só a linha do próprio usuário';
  assert m.consultas = 3 and m.consultas_avaliadas = 2, 'consultas: ' || m.consultas || '/' || m.consultas_avaliadas;
  assert m.looks_mostrados = 9 and m.looks_aprovados = 1, 'looks: ' || m.looks_mostrados || '/' || m.looks_aprovados;
  assert abs(m.hit_rate_3 - 0.5) < 1e-6, 'hit_rate_3 deveria ser 1/2, veio ' || m.hit_rate_3;
  assert abs(m.precision_3 - 1.0 / 6) < 1e-6, 'precision_3 deveria ser 1/6, veio ' || m.precision_3;
  assert (select usos from public.usos_recentes(10) u
           join public.pecas p on p.id = u.peca_id where p.categoria = 'tenis') = 9,
    'usos_recentes deveria contar 9 usos do tênis';
  assert (select aprovados || '/' || total from public.aprovacao_por_categoria(200)
           where categoria = 'camiseta') = '1/4', 'aprovacao_por_categoria da camiseta deveria ser 1/4';
  assert (select count(*) from public.aprovacao_por_categoria(1)) > 0
     and (select max(total) from public.aprovacao_por_categoria(1)) = 1,
    'o limite de feedbacks deveria ser respeitado';
end $$;

select pg_temp.entrar(:'B');
do $$ begin
  assert (select count(*) from public.metricas_recomendacao) = 0, 'B enxergou as métricas de A';
  assert (select count(*) from public.usos_recentes(10)) = 0, 'B enxergou o histórico de A';
end $$;

-- ----------------------------------------------------------- pesos
select pg_temp.entrar(:'A');
do $$ begin
  update public.preferencias
     set pesos = '{"ocasiao":0.4,"clima":0.2,"cor":0.2,"estilo":0.1,"variedade":0.1}';
  begin
    update public.preferencias set pesos = '{"ocasiao":0.9,"clima":0.9,"cor":0.2,"estilo":0.1,"variedade":0.1}';
    assert false, 'pesos somando 2,2 deveriam ser recusados';
  exception when check_violation then null; end;
  begin
    update public.preferencias set pesos = '{"ocasiao":1}';
    assert false, 'pesos com chave faltando deveriam ser recusados';
  exception when check_violation then null; end;
  begin
    update public.preferencias set pesos = '{"ocasiao":"x","clima":0.2,"cor":0.2,"estilo":0.1,"variedade":0.1}';
    assert false, 'peso não numérico deveria ser recusado';
  exception when check_violation then null; end;
end $$;

-- ------------------------------------------------------ consentimento
insert into public.consentimentos (usuario_id, versao, finalidades)
values (:'A', '2026-11-v1', '{"essencial": true, "localizacao": false}');
do $$
declare n int;
begin
  update public.consentimentos set versao = 'adulterado';
  get diagnostics n = row_count;
  assert n = 0, 'o cliente não deveria conseguir editar o registro de consentimento';
  begin
    insert into public.consentimentos (usuario_id, versao)
    values ('22222222-2222-2222-2222-222222222222', 'x');
    assert false, 'A registrou consentimento em nome de B';
  exception when insufficient_privilege then null; end;
  perform public.revogar_consentimento();
  assert (select revogado_em is not null from public.consentimentos), 'a revogação deveria carimbar a data';
end $$;
select pg_temp.entrar(:'B');
do $$ begin
  assert (select count(*) from public.consentimentos) = 0, 'B enxergou o consentimento de A';
end $$;

-- --------------------------------------------------- exclusão da conta
select pg_temp.entrar(:'A');
select public.excluir_minha_conta();
reset role;
do $$
declare a uuid := '11111111-1111-1111-1111-111111111111';
begin
  assert not exists (select 1 from auth.users where id = a), 'usuário não foi removido';
  assert (select count(*) from public.pecas where usuario_id = a)
       + (select count(*) from public.contextos where usuario_id = a)
       + (select count(*) from public.looks where usuario_id = a)
       + (select count(*) from public.feedback where usuario_id = a)
       + (select count(*) from public.consentimentos where usuario_id = a)
       + (select count(*) from public.preferencias where usuario_id = a)
       + (select count(*) from public.perfis where id = a)
       + (select count(*) from public.contador_pecas where usuario_id = a) = 0,
    'sobraram dados do usuário excluído';
  assert (select count(*) from public.look_pecas) = 0, 'sobraram vínculos de looks';
  assert exists (select 1 from auth.users where id = '22222222-2222-2222-2222-222222222222'),
    'a exclusão de A removeu B';
  assert (select count(*) from public.pecas
           where usuario_id = '00000000-0000-0000-0000-0000000000aa') = 3,
    'a exclusão de A mexeu nas peças de outro usuário';
end $$;

-- sem autenticação a função não apaga ninguém
set role anon;
select set_config('request.jwt.claims', '', false);
do $$ begin
  begin
    perform public.excluir_minha_conta();
    assert false, 'anônimo conseguiu chamar excluir_minha_conta';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
\echo 'casos.sql: todos os casos passaram'
