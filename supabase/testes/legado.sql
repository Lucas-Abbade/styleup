-- Dados "antigos", inseridos ANTES das migrações 0003-0005, para provar que
-- elas tratam o que já existe no banco.
insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-0000000000aa', 'legado@teste.dev');

insert into public.pecas (usuario_id, codigo, papel, categoria, cor_nome, cor_hex, cor_hsv, formalidade)
values
  ('00000000-0000-0000-0000-0000000000aa', 'CLO-000001', 'superior', 'camiseta', 'preto', '#000000', '{0,0,0}', 1),
  ('00000000-0000-0000-0000-0000000000aa', 'CLO-000002', 'inferior', 'bermuda',  'bege',  '#d9c6a3', '{38,0.25,0.85}', 1),
  ('00000000-0000-0000-0000-0000000000aa', 'CLO-000003', 'calcado',  'tenis',    'branco','#ffffff', '{0,0,1}', 2);
-- o cenário do defeito: apaga a do meio; count(*)+1 daria CLO-000003 de novo
delete from public.pecas where codigo = 'CLO-000002';

insert into public.contextos (usuario_id, evento, formalidade_alvo, temperatura, latitude, longitude)
values ('00000000-0000-0000-0000-0000000000aa', 'casual', 2, 30, -15.60, -56.10);

update public.preferencias set pesos = '{"ocasiao": 2, "clima": -1}'::jsonb
 where usuario_id = '00000000-0000-0000-0000-0000000000aa';
