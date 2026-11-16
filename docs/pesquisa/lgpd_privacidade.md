# LGPD e orientações da ANPD aplicáveis ao StyleUp (app acadêmico UFMT) — notas de pesquisa (situação em novembro/2026)

> **Aviso.** Notas de engenharia, não parecer jurídico. Pontos marcados com **[REVISAR-DPO]** precisam de validação do encarregado/assessoria jurídica da UFMT.
> **Nota de método.** O site do Planalto bloqueou o acesso automatizado nesta sessão; o texto da LGPD foi conferido em espelho do repositório da CGU ([PDF](https://repositorio.cgu.gov.br/bitstream/1/65216/3/LEI_13709_2018..pdf)) e os links abaixo apontam para a fonte oficial ([Planalto – Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm); [texto compilado](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm)). Trechos entre aspas da lei devem ser conferidos no texto compilado antes de irem para documento formal. Para as Resoluções CD/ANPD nº 2/2022, 15/2024 e 19/2024 só foram acessados resumos de escritórios/blogs (a nº 18/2024 foi lida em espelho do texto integral); a **numeração de artigos dessas resoluções precisa ser conferida no texto oficial** em gov.br/anpd.
> **Mudanças 2025–2026 encontradas:** (i) Lei 15.352, de 25/02/2026, transformou a ANPD em agência reguladora (autarquia especial) e alterou apenas dispositivos institucionais da LGPD (arts. 5º VIII e XIX, 55-A, 55-C), sem mudar obrigações dos agentes — [Confidata](https://confidata.com.br/blog/lgpd-atualizada-2026-o-que-mudou); (ii) Lei 15.211/2025 ("ECA Digital") em vigor desde 17/03/2026, regulamentada pelo Decreto 12.880/2026 — [Câmara](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15211-17-setembro-2025-797997-normaatualizada-pl.html); (iii) Resolução CD/ANPD nº 32, de 26/01/2026, reconheceu a União Europeia/EEE como destino adequado para transferências — [Confidata](https://confidata.com.br/blog/transferencia-internacional-dados-atualizacao-anpd-2026).

---

## 1. Bases legais (art. 7º) por finalidade e requisitos do consentimento válido

### Takeaway
Para o que é indispensável ao funcionamento do app (conta, guarda-roupa, histórico, personalização), a base mais coerente é a execução de contrato/termo de uso a pedido do titular (art. 7º, V); consentimento (art. 7º, I) deve ficar reservado ao que é realmente opcional — a localização. Um "consentimento obrigatório" para a finalidade essencial é juridicamente frágil como consentimento "livre", embora a LGPD admita tratamento como condição do serviço desde que isso seja informado com destaque (art. 9º, §3º). **[REVISAR-DPO]**

### Cited Findings
- Consentimento é definido como "manifestação livre, informada e inequívoca pela qual o titular concorda com o tratamento de seus dados pessoais para uma finalidade determinada" (art. 5º, XII) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- As bases do art. 7º incluem consentimento (I), execução de contrato ou de procedimentos preliminares de que o titular seja parte, a pedido dele (V), estudos por órgão de pesquisa (IV) e legítimo interesse (IX) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Art. 8º: o consentimento deve ser dado por escrito ou outro meio que demonstre a vontade do titular; se escrito, em cláusula destacada (§1º); o ônus da prova é do controlador (§2º); é vedado tratamento com vício de consentimento (§3º); deve referir-se a finalidades determinadas, sendo nulas autorizações genéricas (§4º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Art. 8º, §5º: a revogação pode ocorrer a qualquer momento, por manifestação expressa, "por procedimento gratuito e facilitado", ficando ratificados os tratamentos anteriores enquanto não houver pedido de eliminação (art. 18, VI) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Art. 8º, §6º e art. 9º, §2º: alteração de finalidade, forma/duração, identificação do controlador ou compartilhamento deve ser informada com destaque; se a nova finalidade não for compatível com o consentimento original, o titular deve ser avisado previamente e pode revogar — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Art. 9º, §3º: quando o tratamento for condição para fornecer o serviço, o titular deve ser informado "com destaque" sobre isso e sobre como exercer os direitos do art. 18; art. 18, VIII garante informação sobre a possibilidade de não consentir e as consequências da negativa — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- No Guia de Cookies (out/2022), a ANPD descreve consentimento livre como escolha real, sem consequências negativas que viciem a decisão; veda opções pré-marcadas e consentimento tácito; exige finalidades específicas; pede revogação por procedimento simples, gratuito e semelhante ao da obtenção; e indica que o tratamento estritamente necessário se apoia em outras bases legais, sem hierarquia entre elas — [Machado Meyer, resumo do guia](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/direito-digital/anpd-divulga-novo-guia-com-orientacoes-sobre-cookies)
- No contexto acadêmico, a ANPD lista como bases possíveis o consentimento, estudos por órgão de pesquisa e legítimo interesse, e lembra que as regras de consentimento (arts. 7º §§4º e 6º, 8º, 9º, 18) continuam valendo — [Guia ANPD fins acadêmicos, pp. 22–25](https://ouvidoria.unifesspa.edu.br/images/Documentos/Guia-tratamento-de-dados-para-fins-academicos.pdf)

### Inferences
- **Mapa sugerido de bases legais [REVISAR-DPO]:**

| Finalidade | Dados | Base sugerida | Observação |
|---|---|---|---|
| Criar/manter conta e autenticar | e-mail, nome | art. 7º, V | condição do serviço — informar com destaque (art. 9º §3º) |
| Guarda-roupa digital | recorte da peça, categoria, cor | art. 7º, V | — |
| Gerar looks e histórico | looks gerados, like/dislike | art. 7º, V | — |
| Personalização | pesos de preferência | art. 7º, V (núcleo do serviço) ou IX | se for tratada como "extra", oferecer opção de desligar |
| Clima por localização | coordenadas aproximadas (transitórias) | art. 7º, I (consentimento) | opcional; oferecer alternativa (cidade manual / sem clima) |
| Avaliação acadêmica do recomendador (relatório/TCC) | dados agregados/anonimizados de uso | art. 7º, IV se a UFMT for controladora; ou consentimento específico | finalidade distinta de "entregar o serviço": precisa constar do termo |
| Prova de aceite/consentimento | registro em `consentimentos` | art. 7º, II/VI ou IX (art. 8º §2º impõe o ônus da prova) | definir prazo de guarda |

- O bloqueio (403) até aceitar a versão vigente é compatível com a lei se enquadrado como **aceite do termo de uso** (contrato) e ciência do aviso de privacidade; chamá-lo de "consentimento essencial obrigatório" cria contradição com "livre". Manter o registro do aceite continua útil (prova de transparência).
- Se a equipe mantiver consentimento como base de tudo (por exigência do comitê de ética/TCLE, por exemplo), o termo precisa dizer claramente que recusar ou revogar a finalidade essencial impede o uso do app (arts. 9º §3º e 18 VIII) e a revogação deve equivaler a encerrar a conta.
- O bloqueio 403 **não deve** alcançar as rotas de exercício de direitos (exportar dados, revogar, excluir conta): o titular que não aceita a nova versão precisa conseguir sair e levar/apagar seus dados.
- O consentimento de localização deve ser desmarcado por padrão, separado do aceite essencial e pedido no momento em que o recurso é usado (além da permissão do sistema operacional).

### Gaps
- Não foi localizado guia geral da ANPD dedicado a consentimento (há o de Cookies e o de Legítimo Interesse, de 2024 — este não foi consultado nesta sessão).
- Se o termo de uso de um app gratuito e acadêmico basta como "contrato" para o art. 7º, V é interpretação — confirmar com o DPO.

---

## 2. O que informar ao titular (art. 9º) e o que registrar para provar o consentimento

### Takeaway
O termo/aviso precisa cobrir os sete itens do art. 9º (finalidade específica, forma e duração, controlador e contato, compartilhamento, responsabilidades, direitos do art. 18). A tabela `consentimentos` atual (usuário, data/hora, versão, finalidades) atende ao núcleo da prova; faltam o texto imutável de cada versão, o evento de revogação e o meio de coleta.

### Cited Findings
- O art. 9º exige acesso facilitado, de forma clara, adequada e ostensiva, a: I finalidade específica; II forma e duração; III identificação do controlador; IV contato do controlador; V uso compartilhado e sua finalidade; VI responsabilidades dos agentes; VII direitos do titular com menção explícita ao art. 18 — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O consentimento é nulo se as informações forem enganosas, abusivas ou não apresentadas previamente com transparência (art. 9º, §1º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O ônus de provar que o consentimento foi obtido conforme a lei é do controlador (art. 8º, §2º); o princípio da responsabilização exige demonstrar a adoção de medidas eficazes (art. 6º, X) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Controlador e operador devem manter registro das operações de tratamento (art. 37); para agentes de pequeno porte a ANPD admite registro simplificado — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm); [Mayer Brown, resumo da Res. 2/2022](https://www.mayerbrown.com/-/media/files/perspectives-events/publications/2022/02/regulation-for-the-application-of-the-general-data-protection-law-lgpd-for-small-business-data-processing-agents/legal-update--regulamento-agentes-de-pequeno-porte.pdf)
- A ANPD recomenda aviso em camadas (primeira camada curta com link; segunda camada detalhada), informação clara e simplificada, em português — [Machado Meyer, resumo do Guia de Cookies](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/direito-digital/anpd-divulga-novo-guia-com-orientacoes-sobre-cookies)

### Inferences
- **Campos recomendados para o registro de consentimento/aceite** (log somente-inserção, um evento por ação): `user_id`; `evento` (aceite/consentimento/revogação); `finalidade` (uma linha por finalidade); `versao_termo`; `hash_sha256_do_texto` exibido; `timestamp` (UTC); `meio` (tela/fluxo, ex.: "onboarding-checkbox", "perfil-toggle"); versão do app/plataforma; idioma. Guardar também o **texto integral de cada versão** em repositório versionado.
- Evitar gravar IP/user-agent completos só para "provar" consentimento: a lei não os exige e isso contraria a minimização (art. 6º, III); versão do app + timestamp + hash do texto costumam bastar. **[REVISAR-DPO]**
- Após a exclusão da conta há tensão entre apagar tudo e manter a prova: opção prudente é manter o evento de consentimento pseudonimizado (hash do id) por prazo curto e declarado no aviso; decidir com o DPO.
- Para um projeto pequeno, uma planilha/markdown com "dado – finalidade – base legal – onde fica – com quem é compartilhado – prazo" funciona como registro simplificado de operações (art. 37).

### Gaps
- Nenhuma norma da ANPD encontrada lista campos obrigatórios de um registro de consentimento; os campos acima são boa prática inferida do art. 8º, §2º.

---

## 3. Geolocalização: é dado sensível? Como aplicar necessidade/minimização

### Takeaway
Localização não consta do rol de dados sensíveis do art. 5º, II; é dado pessoal comum, mas de risco elevado porque pode revelar endereço e hábitos. O desenho atual (não armazenar, arredondar ~1 km, uso transitório) está alinhado ao princípio da necessidade; o que falta é arredondar já no dispositivo, garantir que coordenadas não fiquem em logs e documentar o envio ao Open-Meteo.

### Cited Findings
- O rol de dado sensível (art. 5º, II) abrange origem racial/étnica, convicção religiosa, opinião política, filiação sindical ou a organização religiosa/filosófica/política, saúde, vida sexual, dado genético ou biométrico — localização não é mencionada — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O regime de dados sensíveis estende-se a qualquer tratamento que revele dados sensíveis e possa causar dano ao titular (art. 11, §1º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Necessidade (art. 6º, III): limitação ao mínimo necessário, com dados pertinentes, proporcionais e não excessivos; segurança desde a concepção (art. 46, §2º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Dados anonimizados deixam de ser dados pessoais, salvo se a reversão for possível com esforços razoáveis (art. 12) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Nos termos do Open-Meteo, a API gratuita pode registrar endereços IP e os logs podem conter coordenadas geográficas, apagados após 90 dias; o operador é a OpenMeteo GmbH, com sede em Bürglen, Suíça, que se declara controladora independente — [Open-Meteo Terms & Privacy](https://open-meteo.com/en/terms)
- O ECA Digital, para serviços acessíveis a menores, prevê restrição ao compartilhamento de geolocalização e aviso prévio de rastreamento (art. 17, §4º, VI) — [Lei 15.211/2025](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15211-17-setembro-2025-797997-normaatualizada-pl.html)

### Inferences
- **Adequado:** não persistir coordenadas e arredondar antes de consultar o clima. Como a chamada ao Open-Meteo sai do servidor (IP do backend, sem identificador do usuário), o que chega ao terceiro tende a não ser dado pessoal identificável (art. 12) — ainda assim deve ser divulgado no aviso.
- **Faltando / melhorar:**
  1. Arredondar **no cliente** (o backend hoje ainda recebe a coordenada precisa); pedir ao SO apenas localização aproximada (Android `ACCESS_COARSE_LOCATION`; iOS precisão reduzida).
  2. Enviar coordenadas no corpo (POST), não na query string, e conferir que não aparecem em logs de acesso, de erro, de APM ou do Supabase.
  3. Cache de clima por célula/intervalo (reduz chamadas e correlação temporal).
  4. Alternativa sem localização (cidade escolhida manualmente ou sugestão sem clima), para que o consentimento seja de fato opcional.
  5. Revogação no perfil deve também parar de solicitar a permissão/enviar coordenadas imediatamente.
- Com ~10 usuários, uma célula de 1 km + horário pode ser reidentificável por quem conhece os participantes; tratar a coordenada, dentro do backend, sempre como dado pessoal.

### Gaps
- Não encontrei manifestação da ANPD classificando localização como dado sensível; há debate doutrinário sobre o rol ser taxativo e sobre inferência de dados sensíveis a partir de localização — fonte doutrinária não pôde ser aberta nesta sessão.

---

## 4. Fotos: quando imagem é dado biométrico/sensível; fotos de roupas; riscos incidentais

### Takeaway
O recorte de uma peça de roupa vinculado à conta de um usuário é dado pessoal comum (informação relacionada a pessoa identificada), não biométrico. O risco está no que entra "de carona": pessoas, rostos, interior da casa, metadados EXIF e peças que revelem religião/política/saúde — por isso descartar o original e guardar só o recorte é a medida central, mas precisa ser verificável.

### Cited Findings
- Dado pessoal é a informação relacionada a pessoa natural identificada ou identificável (art. 5º, I); dado biométrico só entra no rol sensível "quando vinculado a uma pessoa natural" (art. 5º, II) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Tratamento que revele dado sensível e possa causar dano atrai o regime do art. 11 (art. 11, §1º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- A agenda regulatória 2025–2026 da ANPD mantinha "dados sensíveis – dados biométricos" como tema em desenvolvimento (jan/2026), sem norma final noticiada — [Demarest](https://www.demarest.com.br/anpd-publica-relatorio-de-execucao-da-agenda-regulatoria-2025-2026/)
- Decisões tomadas unicamente por tratamento automatizado que afetem interesses do titular, incluindo definição de perfil de consumo, dão direito a pedir revisão e informações sobre critérios (art. 20) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

### Inferences
- Uma fotografia de pessoa não é automaticamente "dado biométrico": o enquadramento depende de tratamento técnico para identificação única (ex.: template facial). O StyleUp não faz isso; evitar qualquer recurso de reconhecimento facial/corporal.
- Peças podem revelar dado sensível por inferência (vestes religiosas, camisetas de partido/sindicato, itens médicos). Mitigação: não derivar atributos além de categoria e cor; não criar rótulos como "religioso".
- **Checklist técnico para fotos:** (a) remover EXIF (inclui GPS) antes de qualquer gravação; (b) apagar o original e arquivos temporários logo após a segmentação, inclusive em caso de erro; (c) mostrar o recorte ao usuário para confirmação antes de salvar; (d) orientar no app: "fotografe só a peça, sem pessoas, rostos ou documentos"; (e) bucket privado com RLS por usuário e URLs assinadas de curta duração; (f) se a remoção de fundo usar API de terceiro, isso é compartilhamento com operador (e possível transferência internacional) e deve constar do aviso.
- Pesos de preferência são perfilamento de baixo impacto; basta transparência no aviso e, idealmente, um botão "zerar preferências".

### Gaps
- Estudos técnicos da ANPD sobre biometria/reconhecimento facial não foram consultados; a distinção "foto x dado biométrico" acima é inferência a partir do texto legal.

---

## 5. Direitos do titular (art. 18), prazos (art. 19), eliminação (art. 16), backups/logs, pós-revogação

### Takeaway
Exportação em JSON, revogação no perfil e exclusão de conta cobrem os direitos mais relevantes. Faltam: incluir tudo na exportação (fotos, consentimentos, pesos, com quem os dados são compartilhados), apagar também o usuário do Supabase Auth, tratar backups/logs/cache e definir o que acontece após a revogação — a leitura conjunta dos arts. 8º §5º, 15 III e 16 indica que a revogação encerra o tratamento e os dados devem ser eliminados salvo outra base ou exceção, embora os tratamentos anteriores fiquem ratificados até o pedido de eliminação.

### Cited Findings
- Art. 18 garante: I confirmação; II acesso; III correção; IV anonimização, bloqueio ou eliminação de dados desnecessários/excessivos; V portabilidade (conforme regulamentação); VI eliminação dos dados tratados com consentimento, exceto hipóteses do art. 16; VII informação sobre compartilhamento; VIII informação sobre não consentir e consequências; IX revogação — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O pedido é gratuito (art. 18, §5º); se não for possível atender de imediato, o controlador responde indicando as razões (§4º); correção/eliminação deve ser comunicada a quem recebeu os dados (§6º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Art. 19: confirmação/acesso em formato simplificado imediatamente, ou declaração clara e completa (origem, critérios, finalidade) em até 15 dias; dados guardados em formato que favoreça o acesso (§1º); quando o tratamento se basear em consentimento ou contrato, o titular pode pedir cópia eletrônica integral em formato que permita uso posterior (§3º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Eliminação é a "exclusão de dado ou de conjunto de dados armazenados em banco de dados, independentemente do procedimento empregado" (art. 5º, XIV) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O tratamento termina, entre outros casos, por comunicação do titular, inclusive revogação do consentimento (art. 15, III); encerrado o tratamento, os dados são eliminados, admitida a conservação para obrigação legal/regulatória, estudo por órgão de pesquisa (anonimizando sempre que possível), transferência a terceiro e uso exclusivo do controlador com dados anonimizados (art. 16, I–IV) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Para agentes de pequeno porte, os prazos de resposta ao titular e da declaração completa do art. 19, II são contados em dobro, e a declaração simplificada pode ser entregue em até 15 dias — [Mayer Brown, Res. 2/2022](https://www.mayerbrown.com/-/media/files/perspectives-events/publications/2022/02/regulation-for-the-application-of-the-general-data-protection-law-lgpd-for-small-business-data-processing-agents/legal-update--regulamento-agentes-de-pequeno-porte.pdf)
- Em janeiro/2026 o regulamento da ANPD sobre direitos dos titulares ainda constava como "em desenvolvimento" — [Demarest](https://www.demarest.com.br/anpd-publica-relatorio-de-execucao-da-agenda-regulatoria-2025-2026/)
- No Supabase, banco, Auth, Storage e backups ficam na região AWS escolhida pelo cliente; logs são ingeridos em data centers na UE e conteúdo do Storage pode ser servido por CDN global — [Supabase Data Residency FAQ](https://supabase.com/legal/privacy-resources/data-residency-and-transfers-faq)

### Inferences
- **Exportação JSON — completar:** dados de conta; itens e atributos; **arquivos das fotos** (ZIP ou URLs assinadas); looks e feedback; pesos de preferência; eventos de consentimento; lista de operadores/destinatários (art. 18, VII); finalidade e origem de cada grupo de dados (art. 19, II).
- **Exclusão de conta — completar:** (1) apagar o usuário em `auth.users` (API admin), não só as tabelas da aplicação; (2) apagar objetos do Storage e invalidar cache/CDN e URLs assinadas; (3) apagar caches locais no dispositivo e sessões/tokens; (4) declarar no aviso a janela em que cópias de segurança ainda contêm os dados e garantir que uma restauração reaplique as exclusões; (5) logs: não conter dados pessoais ou ter retenção curta; (6) registrar que a exclusão ocorreu sem guardar dados pessoais; (7) confirmação na tela/e-mail ao usuário.
- **Pós-revogação [REVISAR-DPO]:** revogação da localização → parar imediatamente (nada a apagar, pois não há armazenamento). Revogação/recusa da finalidade essencial → equivalente a encerrar o uso: oferecer exclusão imediata e, se o usuário não excluir, eliminar automaticamente após prazo curto e anunciado (ex.: 30 dias). Manter dados indefinidamente "até o usuário pedir" é difícil de sustentar frente aos arts. 15, III e 16.
- **Retenção:** fixar data de encerramento do projeto e apagar tudo (ou anonimizar o que for para o relatório acadêmico) nessa data; prever exclusão por inatividade.
- Prazo operacional recomendado: atender pedidos pelo app de imediato e pedidos por e-mail em até 15 dias.
- Correção (art. 18, III): permitir editar nome, categoria e cor das peças.

### Gaps
- Não confirmei se o regulamento de direitos dos titulares foi publicado entre fev. e nov./2026; verificar em gov.br/anpd.
- Política de backups do plano Supabase usado (existência, retenção, PITR) não verificada.
- Não localizei orientação da ANPD específica sobre eliminação em backups; a prática descrita é inferência.

---

## 6. Crianças e adolescentes (art. 14), Enunciado nº 1/2023 e ECA Digital

### Takeaway
A opção mais simples e segura é restringir o teste a maiores de 18 anos por **controle de recrutamento** (convite/lista de e-mails de participantes cuja idade a equipe conhece), não só pela caixa "tenho 18+". Admitir alunos de 17 anos aciona o art. 14 da LGPD (melhor interesse), a Lei 15.211/2025 (ECA Digital, em vigor desde 17/03/2026) e, provavelmente, autorização de responsável — complexidade desproporcional para um teste com ~10 pessoas. **[REVISAR-DPO]**

### Cited Findings
- Art. 14: tratamento de dados de crianças e adolescentes deve atender ao seu melhor interesse (caput); para crianças, exige consentimento específico e em destaque de um dos pais/responsável (§1º); o controlador deve publicar tipos de dados, uso e forma de exercer direitos (§2º); não pode condicionar jogos/aplicações a dados além do estritamente necessário (§4º); deve empregar esforços razoáveis para verificar o consentimento parental (§5º); a informação deve ser simples e acessível (§6º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O Enunciado CD/ANPD nº 1/2023 (publicado em 24/05/2023) admite tratar dados de crianças e adolescentes com base nas hipóteses do art. 7º ou do art. 11, desde que o melhor interesse seja observado e prevaleça, avaliado no caso concreto — [Felsberg](https://www.felsberg.com.br/importante-anpd-publica-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes/)
- A Lei 15.211/2025 aplica-se a produtos/serviços de TI direcionados a crianças e adolescentes ou de "acesso provável" por eles, definido por três situações: suficiente probabilidade de uso e atratividade (I), considerável facilidade de acesso (II) e significativo grau de risco à privacidade, segurança ou desenvolvimento (III); os conceitos de criança/adolescente remetem ao ECA (art. 2º, §1º) — [Lei 15.211/2025](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15211-17-setembro-2025-797997-normaatualizada-pl.html)
- A mesma lei exige configurações de privacidade mais protetivas por padrão (art. 7º), mecanismos confiáveis de verificação de idade a cada acesso a conteúdo impróprio para menores de 18, vedada a autodeclaração (art. 9º, §1º), uso dos dados de aferição de idade só para esse fim (art. 13) e sanções de advertência a multa de até 10% do faturamento ou R$ 10–1.000 por usuário, limitada a R$ 50 milhões (art. 35); a vigência em 17/03/2026 foi fixada pelo art. 41-A (Lei 15.352/2026) — [Lei 15.211/2025](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15211-17-setembro-2025-797997-normaatualizada-pl.html)
- Orientações preliminares da ANPD sobre aferição de idade, baseadas em risco, consideram insuficiente a autodeclaração isolada e recomendam cautela com soluções intrusivas como biometria; o Decreto 12.880/2026 regulamenta a lei — [Chambers](https://chambers.com/articles/eca-digital-é-regulamentado-e-anpd-publica-orientações-sobre-verificação-etária)
- Segundo comentário de mercado, a cobertura não depende de o público declarado ser menor: basta o acesso ser possível na prática; a fiscalização da ANPD sobre aferição de idade foi escalonada (lojas de apps/SO até jun/2026; jogos, marketplaces e redes sociais ago–nov/2026; sanções a partir de jan/2027) — [Confidata](https://confidata.com.br/blog/eca-digital-o-que-muda-empresas)
- Agentes de pequeno porte que tratam dados de crianças/adolescentes podem cair no critério específico de "alto risco" e perder o regime simplificado, se também presente um critério geral — [Confidata, Res. 2/2022](https://confidata.com.br/blog/lgpd-pequenas-empresas-resolucao-pequeno-porte)

### Inferences
- A vedação absoluta de autodeclaração do art. 9º, §1º do ECA Digital mira conteúdo/serviços impróprios para menores, o que não é o caso de um app de guarda-roupa; mas a caixa "18+" sozinha não exclui o enquadramento como serviço de "acesso provável" se o cadastro for aberto ao público.
- **Para o teste acadêmico:** (1) cadastro fechado (allow-list de e-mails ou código de convite); (2) confirmação da maioridade no recrutamento, registrada no termo de participação; (3) manter a declaração 18+ no termo como camada adicional; (4) não publicar em loja de apps com cadastro aberto durante o teste; (5) se surgir conta de menor, excluir conta e dados.
- **Se a equipe decidir incluir participante de 17 anos:** autorização do responsável + assentimento do adolescente, avaliação de melhor interesse documentada, padrões mais protetivos por padrão (localização desligada), linguagem acessível — e validação prévia do DPO/comitê de ética.

### Gaps
- Não ficou claro, nas fontes lidas, se as três situações de "acesso provável" são cumulativas ou alternativas; há estudo da Data Privacy Brasil sobre o conceito (não consultado): [PDF](https://www.dataprivacybr.org/wp-content/uploads/2026/01/20260304_acesso-provavel-Eca-Digital.pdf).
- Texto das orientações preliminares da ANPD sobre aferição de idade e do Decreto 12.880/2026 não foi lido na íntegra; nenhum deles, nas fontes vistas, trata de projetos acadêmicos de pequena escala.
- Regras civis de capacidade (16–18 anos) e exigências de comitê de ética para menores não foram pesquisadas.

---

## 7. Transferência internacional (arts. 33–36; Resolução CD/ANPD nº 19/2024)

### Takeaway
Usar Supabase é, em regra, transferência internacional (ainda que o projeto esteja em São Paulo, há logs na UE e suporte/contas em Singapura/EUA). O caminho prático para um controlador pequeno: criar/migrar o projeto para `sa-east-1`, aceitar o DPA do Supabase, declarar no aviso países, finalidade e operadores, e — como o DPA não menciona cláusulas-padrão brasileiras — apoiar a transferência residual em hipótese do art. 33 adequada (IX, se a base for contrato; ou VIII, consentimento específico e destacado). **[REVISAR-DPO]**

### Cited Findings
- Art. 33 só permite transferência internacional em hipóteses taxativas, entre elas: país com proteção adequada (I); garantias como cláusulas-padrão, cláusulas específicas, normas corporativas globais, selos/certificados (II); consentimento específico e em destaque, com informação prévia do caráter internacional (VIII); necessidade para atender às hipóteses do art. 7º, II, V e VI (IX) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- A Resolução CD/ANPD nº 19, de 23/08/2024, regulamenta os arts. 33–36, aprova as cláusulas-padrão contratuais (CPCs) e deu 12 meses para incorporá-las — prazo encerrado em 23/08/2025; serviços SaaS que processam dados no exterior e replicação para região fora do Brasil são exemplos de transferência — [Confidata](https://confidata.com.br/blog/transferencia-internacional-dados-atualizacao-anpd-2026)
- As CPCs devem ser adotadas integralmente e sem alteração; o controlador deve publicar em seu site documento (pode ser parte da política de privacidade) com informações sobre a transferência, incluindo país de destino e identificação/contato do controlador, e fornecer a íntegra das cláusulas em 15 dias quando o titular pedir — [Conjur](https://www.conjur.com.br/2024-set-01/regulamento-sobre-transferencia-internacional-de-dados/)
- A Resolução CD/ANPD nº 32, de 26/01/2026, reconhece adequação da União Europeia e do EEE (30 países); demais países são avaliados individualmente — [Confidata](https://confidata.com.br/blog/transferencia-internacional-dados-atualizacao-anpd-2026)
- Recomendações práticas a quem usa nuvem estrangeira: verificar onde os dados são processados e a lista de suboperadores; checar se o DPA incorpora as CPCs da ANPD; manter inventário de transferências; mesmo com região brasileira, suporte/backup podem ocorrer em outras regiões — [Confidata](https://confidata.com.br/blog/transferencia-internacional-dados-atualizacao-anpd-2026)
- Supabase: o cliente escolhe a região; `sa-east-1` (São Paulo) está disponível — [Supabase Regions](https://supabase.com/regions)
- Supabase: fora da região escolhida ficam dados de conta/faturamento (sistemas centralizados), acesso de suporte global, telemetria/logs (ingeridos em data centers na UE) e eventual CDN global; o operador principal é a Supabase Pte. Ltd. (Singapura), com apoio da Supabase, Inc. (EUA); o DPA incorpora cláusulas-padrão europeias e a página não menciona Brasil/LGPD — [Supabase Data Residency FAQ](https://supabase.com/legal/privacy-resources/data-residency-and-transfers-faq)
- Open-Meteo é operado por empresa suíça — [Open-Meteo Terms](https://open-meteo.com/en/terms)

### Inferences
- A Suíça não integra UE/EEE, logo a decisão de adequação da Res. 32/2026 não cobre o Open-Meteo; porém o que o backend envia (coordenada arredondada, sem identificador, a partir do IP do servidor) tende a não ser dado pessoal — manter assim e declarar no aviso.
- **O que fazer na prática:** (1) confirmar a região atual do projeto Supabase; se não for `sa-east-1`, migrar (dados em repouso no Brasil reduzem o problema); (2) aceitar/assinar o DPA e guardar cópia; (3) listar no aviso: Supabase (Singapura/EUA; logs na UE; dados em repouso em [região]) e Open-Meteo (Suíça); (4) registrar a hipótese do art. 33 usada; (5) avaliar um checkbox específico e destacado de transferência internacional (art. 33, VIII) como salvaguarda simples para ~10 usuários; (6) manter inventário de suboperadores.
- Se a UFMT for a controladora, verificar se a universidade admite hospedar dados de projetos em nuvem estrangeira contratada em conta pessoal de aluno. **[REVISAR-DPO]**

### Gaps
- Número do artigo do dever de transparência no regulamento da Res. 19/2024 não confirmado no texto oficial.
- O blog que noticia a Res. 32/2026 tem inconsistência de datas (página datada de dez/2025 descrevendo norma de jan/2026); confirmar número/data no DOU ou no site da ANPD.
- Não verifiquei se o DPA mais recente do Supabase (há versão de jun/2026 listada em [supabase.com/legal/dpa](https://supabase.com/legal/dpa)) passou a incluir as CPCs brasileiras.

---

## 8. Agentes de pequeno porte, exceção acadêmica, encarregado e quem é o controlador

### Takeaway
A exceção de "fins exclusivamente acadêmicos" (art. 4º, II, b) é restritiva, mantém a exigência de base legal (arts. 7º e 11) e dificilmente cobre um app operado com usuários reais — tratar o StyleUp como plenamente sujeito à LGPD. Quem é o controlador (UFMT ou os estudantes) precisa ser definido formalmente: disso depende se vale o regime de pequeno porte (encarregado dispensado, prazos em dobro) ou o encarregado e as regras do setor público da universidade. **[REVISAR-DPO]**

### Cited Findings
- A LGPD não se aplica ao tratamento para fins exclusivamente acadêmicos, mas nessa hipótese continuam aplicáveis os arts. 7º e 11 (art. 4º, II, b); também não se aplica a pessoa natural para fins exclusivamente particulares e não econômicos (art. 4º, I) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Para a ANPD, a exceção acadêmica deve ser interpretada restritivamente, limitada ao tratamento estritamente vinculado à liberdade acadêmica; para outras finalidades a LGPD incide plenamente; o tratamento precisa ser sempre lícito; exige-se definição clara das responsabilidades de cada agente (pp. 19–22) — [Guia ANPD fins acadêmicos](https://ouvidoria.unifesspa.edu.br/images/Documentos/Guia-tratamento-de-dados-para-fins-academicos.pdf)
- O mesmo guia qualifica universidades como exemplos de órgão de pesquisa (art. 5º, XVIII), remete pesquisas com seres humanos ao sistema CEP/CONEP (p. 44), observa que o consentimento ético pode ser exigido mesmo quando a LGPD não o exija (p. 45) e, para estudantes, sugere termo de ciência e responsabilidade assinado por agente institucional como o orientador (p. 40) — [Guia ANPD fins acadêmicos](https://ouvidoria.unifesspa.edu.br/images/Documentos/Guia-tratamento-de-dados-para-fins-academicos.pdf)
- No Guia de Agentes de Tratamento, a ANPD afirma que indivíduos subordinados — funcionários, servidores públicos, equipes de trabalho — não são controladores nem operadores; pessoa natural é controladora quando decide, em interesse próprio, finalidades e elementos essenciais do tratamento — [Migalhas, resumo do guia](https://www.migalhas.com.br/depeso/346394/anpd-define-que-funcionario-e-servidor); guia oficial: [gov.br/anpd](https://www.gov.br/anpd/pt-br/documentos-e-publicacoes/Segunda_Versao_do_Guia_de_Agentes_de_Tratamento_retificada.pdf/)
- A Resolução CD/ANPD nº 2/2022 considera agentes de pequeno porte microempresas, EPPs, startups, pessoas jurídicas sem fins lucrativos, pessoas naturais e entes despersonalizados que assumem obrigações típicas de controlador/operador; exclui quem faz tratamento de alto risco (um critério geral — larga escala ou afetar significativamente direitos — mais um específico: tecnologia emergente/inovadora, vigilância, decisão unicamente automatizada, dados sensíveis ou de crianças, adolescentes e idosos) — [Mayer Brown](https://www.mayerbrown.com/-/media/files/perspectives-events/publications/2022/02/regulation-for-the-application-of-the-general-data-protection-law-lgpd-for-small-business-data-processing-agents/legal-update--regulamento-agentes-de-pequeno-porte.pdf)
- Flexibilizações: registro de operações simplificado, dispensa de encarregado com manutenção de canal de comunicação, política de segurança simplificada, comunicação de incidente simplificada e prazos em dobro; princípios, bases legais e direitos dos titulares continuam obrigatórios — [Mayer Brown](https://www.mayerbrown.com/-/media/files/perspectives-events/publications/2022/02/regulation-for-the-application-of-the-general-data-protection-law-lgpd-for-small-business-data-processing-agents/legal-update--regulamento-agentes-de-pequeno-porte.pdf); [Confidata](https://confidata.com.br/blog/lgpd-pequenas-empresas-resolucao-pequeno-porte)
- Resolução CD/ANPD nº 18/2024: indicação do encarregado por ato formal escrito, datado e assinado (art. 3º, §§1º–2º); agentes de pequeno porte dispensados devem oferecer canal de comunicação com o titular (art. 3º, §3º, remetendo ao art. 11 da Res. 2/2022); identidade (nome completo) e contato divulgados em local de destaque no site ou outro meio usual (arts. 8º–9º); comunicação em português (art. 13); o agente de tratamento permanece responsável pela conformidade (arts. 11 e 17) — [Res. CD/ANPD 18/2024, texto](https://www.tjba.jus.br/extrajudicial/wp-content/uploads/2024/08/RESOLUCAO-ANPD-No-18-Encarregado-de-Dados.pdf)
- Em junho/2026 a ANPD concluiu a primeira fase de monitoramento sobre encarregados e canais de atendimento ao titular, encaminhando 21 organizações à área sancionadora — [Confidata](https://confidata.com.br/blog/lgpd-atualizada-2026-o-que-mudou)

### Inferences
- **Cenário A — UFMT controladora** (projeto de disciplina/TCC, orientado por docente, usando o nome da universidade): estudantes e professor atuam como equipe subordinada, não como controladores; aplica-se o encarregado da UFMT e o regime do poder público; a Res. 2/2022 não se aplica (órgãos públicos não estão na lista de agentes de pequeno porte); estudos podem se apoiar no art. 7º, IV.
- **Cenário B — estudantes controladores** (decidem finalidades e meios por conta própria, infraestrutura em contas pessoais): pessoas naturais podem ser agentes de pequeno porte; com ~10 usuários adultos, sem dados sensíveis e sem larga escala, o tratamento não parece de alto risco → encarregado dispensado, mas com e-mail de contato publicado; prazos em dobro; registro simplificado.
- A exceção do art. 4º, I (uso particular) não se aplica: há oferta de serviço a terceiros.
- **Ação recomendada:** perguntar por escrito ao encarregado da UFMT (i) quem figura como controlador; (ii) se é preciso submissão a comitê de ética (coleta de feedback de participantes); (iii) qual contato vai no termo. Até lá, o termo deve identificar a equipe, o orientador, o vínculo com a UFMT e um e-mail de contato funcional.

### Gaps
- Nenhuma fonte encontrada trata expressamente de projeto de disciplina com app operado por alunos; a definição do controlador é caso a caso.
- Nome/contato do encarregado da UFMT e eventual norma interna da universidade sobre projetos estudantis não foram pesquisados.
- Texto integral da Res. 2/2022 não foi lido (numeração de artigos a confirmar).

---

## 9. Segurança (arts. 46–49) e comunicação de incidentes (art. 48; Resolução CD/ANPD nº 15/2024) — caso do segredo JWT exposto em captura de tela

### Takeaway
A exposição de um segredo de assinatura JWT deve ser tratada como incidente de segurança: rotacionar imediatamente, investigar acessos e registrar internamente (o registro é obrigatório por 5 anos mesmo sem comunicação). Só há dever de comunicar à ANPD e aos titulares — em 3 dias úteis a contar da ciência de que dados pessoais foram afetados — se o incidente puder afetar significativamente os titulares **e** envolver ao menos uma categoria qualificada (ex.: dados de autenticação em sistemas). **[REVISAR-DPO]**

### Cited Findings
- Agentes devem adotar medidas técnicas e administrativas aptas a proteger os dados contra acessos não autorizados e situações acidentais ou ilícitas (art. 46), desde a concepção do produto (art. 46, §2º); sistemas devem atender a requisitos de segurança e boas práticas (art. 49) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- O controlador deve comunicar à ANPD e ao titular incidente que possa acarretar risco ou dano relevante, descrevendo dados afetados, titulares envolvidos, medidas de segurança, riscos e medidas de mitigação (art. 48 e §1º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Pela Res. CD/ANPD nº 15/2024, há risco ou dano relevante quando o incidente pode afetar significativamente interesses e direitos fundamentais dos titulares e, cumulativamente, envolve ao menos um de: dados sensíveis; dados de crianças, adolescentes ou idosos; dados financeiros; dados de autenticação em sistemas; dados sob sigilo legal, judicial ou profissional; dados em larga escala — [Lefosse](https://lefosse.com/noticias/alerta/client-alert-anpd-aprova-regulamento-de-comunicacao-de-incidente-de-seguranca/)
- "Afetar significativamente" abrange impedir exercício de direitos ou uso de serviço, ou causar danos materiais/morais como discriminação, dano à reputação, fraude financeira ou roubo de identidade — [Lefosse](https://lefosse.com/noticias/alerta/client-alert-anpd-aprova-regulamento-de-comunicacao-de-incidente-de-seguranca/)
- Prazo: 3 dias úteis para comunicar ANPD e titulares, contados do conhecimento de que o incidente afetou dados pessoais; complementação em até 20 dias úteis; registro de incidentes mantido por no mínimo 5 anos, inclusive dos não comunicados — [Lefosse](https://lefosse.com/noticias/alerta/client-alert-anpd-aprova-regulamento-de-comunicacao-de-incidente-de-seguranca/)
- Para agentes de pequeno porte o prazo de comunicação dobra (6 dias úteis), salvo se houver potencial de comprometer a integridade física ou moral dos titulares; incidentes abaixo do limiar devem ser registrados com a avaliação que levou a não notificar — [Confidata](https://confidata.com.br/blog/comunicacao-incidente-seguranca-anpd)
- O guia (não vinculante) da ANPD de segurança para agentes de pequeno porte recomenda: política de segurança; conscientização; cláusulas contratuais; controle de acesso com privilégio mínimo e contas individuais; senhas fortes e autenticação multifator; backups testados; criptografia; conexões cifradas (TLS/HTTPS); sistemas atualizados; cuidados com dispositivos móveis; avaliação de segurança e localização dos serviços em nuvem — [Projuris, resumo do guia](https://www.projuris.com.br/blog/guia-de-seguranca-da-informacao-da-anpd/)

### Inferences
- **Roteiro para o segredo JWT exposto:**
  1. Conter: rotacionar o JWT secret e as chaves derivadas (anon/service_role), invalidar sessões, remover/retificar a captura onde foi publicada (repositório, relatório, chat) e limpar histórico git se aplicável.
  2. Investigar: logs de API/Auth/Storage do período de exposição à procura de acessos anômalos; anotar por quanto tempo e para quem a imagem ficou visível.
  3. Registrar no livro de incidentes: data da ciência, descrição, dados potencialmente afetados (e-mail, nome, fotos, histórico), nº de titulares (~10), medidas, avaliação de risco e decisão sobre comunicar.
  4. Decidir: sem evidência de acesso indevido e com exposição restrita → provável ausência de "risco ou dano relevante" (registrar e não comunicar). Com evidência ou impossibilidade de descartar acesso a dados de usuários (o segredo permite forjar tokens e ler dados de qualquer conta) → comunicar ANPD e titulares no prazo; credenciais de usuários enquadram-se em "dados de autenticação em sistemas".
  5. Avisar orientador e encarregado da UFMT em qualquer caso.
- **Medidas mínimas de segurança/minimização para o StyleUp:** segredos só em variáveis de ambiente/secret manager, nunca em capturas ou repositório (secret scanning no CI); `service_role` apenas no backend; RLS em todas as tabelas e buckets; HTTPS; MFA nas contas Supabase/GitHub da equipe; contas individuais com privilégio mínimo; logs sem e-mail, token, coordenadas ou URL de foto; dependências atualizadas; documento curto de política de segurança e de resposta a incidentes; backup testado.

### Gaps
- Definição formal de "incidente de segurança" e numeração dos artigos da Res. 15/2024 não confirmadas no texto oficial (fontes secundárias divergiram entre si quanto à numeração).
- Não há orientação da ANPD encontrada sobre exposição de segredo sem acesso confirmado; a conclusão acima é inferência.
- Guia de segurança da ANPD lido apenas por resumo.

---

## 10. Boas práticas reconhecidas e avaliação do que já está implementado

### Takeaway
A implementação atual cobre a maior parte do que a LGPD pede a um app desse porte; as lacunas concentram-se em enquadramento jurídico (base legal do "essencial"), completude (exportação, exclusão no Auth, backups, logs), transparência (operadores, países, prazos, contato) e controle de idade por recrutamento.

### Cited Findings
- Princípios aplicáveis: finalidade, adequação, necessidade, transparência, segurança, prevenção e responsabilização (art. 6º, I–III, VI–VIII, X); regras de boas práticas e governança são incentivadas (art. 50) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Aviso em camadas, opções granulares, nada pré-marcado, botões equivalentes e revogação tão simples quanto a concessão são práticas descritas pela ANPD — [Machado Meyer, Guia de Cookies](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/direito-digital/anpd-divulga-novo-guia-com-orientacoes-sobre-cookies)
- Cópia eletrônica integral em formato reutilizável quando a base for consentimento ou contrato (art. 19, §3º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Privacidade mais protetiva por padrão é exigência legal para serviços acessíveis a menores (art. 7º da Lei 15.211/2025) — [Lei 15.211/2025](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15211-17-setembro-2025-797997-normaatualizada-pl.html)
- O Open-Meteo gratuito é restrito a uso não comercial (menos de 10.000 chamadas/dia) e licencia os dados sob CC-BY 4.0 — [Open-Meteo Terms](https://open-meteo.com/en/terms)

### Inferences
**Avaliação item a item (engenharia; [REVISAR-DPO] onde indicado)**

| Já implementado | Avaliação | O que falta |
|---|---|---|
| Coordenadas não armazenadas; arredondadas (~1 km) antes de sair do servidor | Adequado (art. 6º III; art. 46 §2º) | Arredondar no cliente; POST em vez de query string; auditoria de logs; cache; alternativa sem localização |
| Tabela `consentimentos` (usuário, timestamp, versão, finalidades) | Adequado como núcleo de prova (art. 8º §2º) | Hash/texto de cada versão; evento de revogação; meio/tela; log somente-inserção; prazo de guarda |
| Finalidade "essencial" obrigatória + localização opcional separada | Granularidade correta | Reenquadrar "essencial" como aceite do termo de uso (art. 7º V) ou explicitar consequência da recusa (art. 9º §3º; art. 18 VIII) **[REVISAR-DPO]** |
| 403 nas rotas de dados até aceitar a versão vigente | Aceitável | Excluir do bloqueio: exportar, revogar, excluir conta; destacar o que mudou entre versões (art. 8º §6º) |
| Revogação na tela de perfil | Adequado (art. 8º §5º) | Mesmo nº de passos da concessão; efeito imediato; regra pós-revogação/eliminação |
| Download dos dados em JSON | Adequado (art. 18 II; art. 19 §3º) | Incluir fotos, consentimentos, pesos, lista de operadores, finalidades |
| Exclusão de conta apaga linhas e arquivos do usuário | Adequado (art. 18 VI) | Apagar `auth.users`; cache/CDN; backups (janela declarada); logs; confirmação ao usuário |
| Termo diz "18+" | Insuficiente sozinho | Cadastro por convite; verificação de maioridade no recrutamento; procedimento se aparecer menor **[REVISAR-DPO]** |
| Supabase em nuvem + Open-Meteo | A regularizar | Região `sa-east-1`; DPA; seção de transferência internacional no aviso; hipótese do art. 33 **[REVISAR-DPO]** |
| (não informado) contato/encarregado, retenção, registro de operações, plano de incidentes | Faltando | E-mail de contato no termo; data de encerramento/retenção; registro simplificado (art. 37); livro de incidentes |

- Outras práticas: padrão mais protetivo (localização desligada); crédito ao Open-Meteo (CC-BY 4.0); nenhum SDK de analytics/publicidade; dados agregados/anonimizados no relatório acadêmico; botão "zerar preferências".

### Gaps
- Não há, nas fontes consultadas, guia da ANPD específico para aplicativos móveis; as práticas acima derivam da lei, do Guia de Cookies e do guia de segurança.
- A eventual obrigação de guarda de registros de acesso do Marco Civil da Internet (Lei 12.965/2014) para um projeto sem fins econômicos não foi pesquisada.

---

## 11. Checklist e minuta de termo de consentimento/aviso de privacidade (pt-BR) — RASCUNHO, SUJEITO A REVISÃO JURÍDICA

### Takeaway
O termo curto (primeira camada) deve caber em uma tela, citar os itens do art. 9º, separar o aceite necessário do consentimento opcional de localização e apontar para um aviso completo (segunda camada). O texto abaixo é rascunho de pesquisa para ser adaptado e validado pelo encarregado/assessoria da UFMT antes do uso.

### Cited Findings
- Conteúdo mínimo: finalidade específica, forma e duração, controlador e contato, compartilhamento, responsabilidades, direitos do art. 18 (art. 9º, I–VII); destaque quando o tratamento for condição do serviço (art. 9º, §3º); cláusula de consentimento destacada (art. 8º, §1º); finalidades determinadas (art. 8º, §4º); revogação gratuita e facilitada (art. 8º, §5º) — [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Transferência internacional: informar país de destino e identificação/contato do controlador em documento acessível — [Conjur, Res. 19/2024](https://www.conjur.com.br/2024-set-01/regulamento-sobre-transferencia-internacional-de-dados/)
- Contato do encarregado ou, se dispensado, canal de comunicação com o titular, em português — [Res. CD/ANPD 18/2024](https://www.tjba.jus.br/extrajudicial/wp-content/uploads/2024/08/RESOLUCAO-ANPD-No-18-Encarregado-de-Dados.pdf)
- Informação clara, simplificada, em camadas, sem opções pré-marcadas — [Machado Meyer, Guia de Cookies](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/direito-digital/anpd-divulga-novo-guia-com-orientacoes-sobre-cookies)

### Inferences

**Checklist de elementos do termo**
- [ ] Nome do app, versão e data do termo; link para a versão completa e para versões anteriores
- [ ] Quem é o responsável (controlador), vínculo com a UFMT, orientador, e-mail de contato / encarregado
- [ ] Público: maiores de 18 anos, participantes convidados
- [ ] Dados tratados, por finalidade, com base legal
- [ ] Destaque: quais dados são condição para usar o app; o que é opcional
- [ ] Localização: opcional, aproximada, não armazenada, usada só para o clima
- [ ] Fotos: só o recorte da peça é guardado; orientação para não fotografar pessoas
- [ ] Com quem os dados são compartilhados (Supabase, Open-Meteo) e em quais países
- [ ] Por quanto tempo (exclusão de conta, fim do projeto, cópias de segurança)
- [ ] Direitos e como exercê-los no app; prazo de resposta; possibilidade de peticionar à ANPD
- [ ] Como revogar e o que acontece depois
- [ ] Segurança e aviso em caso de incidente
- [ ] Como mudanças no termo serão comunicadas
- [ ] Caixas de aceite separadas, nenhuma pré-marcada; registro de versão, data/hora e finalidade

**Minuta (primeira camada) — RASCUNHO**

> **StyleUp — Termo de uso e privacidade (versão 1.0, de DD/MM/AAAA)**
>
> O StyleUp é um projeto acadêmico de estudantes do curso de [curso] da Universidade Federal de Mato Grosso (UFMT), orientado por [nome do(a) professor(a)]. Responsável pelo tratamento dos dados: [UFMT / nomes dos estudantes — definir]. Contato para qualquer assunto sobre seus dados: [e-mail]. [Encarregado: nome e contato, se aplicável.]
>
> **Para quem é:** pessoas com 18 anos ou mais, convidadas a participar do teste.
>
> **Dados necessários para o app funcionar** (sem eles não é possível usar o StyleUp):
> - **Nome e e-mail** — para criar e acessar sua conta.
> - **Fotos das suas peças de roupa** — guardamos somente o recorte da peça, sem o fundo; a foto original é descartada após o processamento. Registramos também a categoria e a cor da peça. Fotografe apenas a roupa, sem pessoas, rostos ou documentos.
> - **Looks sugeridos e suas avaliações (gostei / não gostei)** — para montar seu histórico e aprender suas preferências, melhorando as próximas sugestões.
>
> **Dado opcional — localização aproximada:** se você autorizar, usamos a localização do aparelho apenas para consultar a previsão do tempo e sugerir roupas adequadas ao clima. A localização é arredondada (cerca de 1 km), **não é armazenada** e é enviada ao serviço de meteorologia sem nenhuma identificação sua. Você pode usar o app sem autorizar e pode desligar essa opção quando quiser em **Perfil > Privacidade**.
>
> **Com quem compartilhamos:** não vendemos seus dados nem os usamos para publicidade. Usamos dois prestadores de serviço: **Supabase** (conta, banco de dados e arquivos; servidores em [região/país]; a empresa tem sede em Singapura e nos EUA e mantém registros técnicos na União Europeia) e **Open-Meteo** (previsão do tempo; Suíça; recebe apenas coordenadas aproximadas). Por isso, parte dos dados pode ser tratada fora do Brasil.
>
> **Por quanto tempo:** até você excluir sua conta ou até o encerramento do projeto em [data], o que ocorrer primeiro. Cópias de segurança são apagadas em até [N] dias. Resultados acadêmicos usarão apenas dados agregados, sem identificar você.
>
> **Seus direitos (LGPD, art. 18):** a qualquer momento, em **Perfil**, você pode ver e corrigir seus dados, **baixar uma cópia** (arquivo JSON), **revogar** a autorização de localização e **excluir sua conta e todos os seus dados**. Também pode pedir informações ou fazer solicitações pelo e-mail acima — respondemos em até 15 dias — e, se necessário, peticionar à Agência Nacional de Proteção de Dados (ANPD).
>
> **Mudanças:** se este termo mudar, avisaremos com destaque o que mudou; se houver nova finalidade, pediremos nova autorização.
>
> Versão completa: [link para o aviso de privacidade].
>
> ☐ Li e aceito o Termo de Uso e estou ciente de como meus dados serão tratados. *(necessário para usar o app)*
> ☐ Declaro que tenho 18 anos ou mais. *(necessário)*
> ☐ Autorizo o uso da minha localização aproximada para consultar o clima. *(opcional — pode ser alterado depois)*
> ☐ Estou ciente e autorizo, de forma específica, que meus dados sejam armazenados e tratados em servidores fora do Brasil, conforme descrito acima. *(incluir somente se o DPO indicar o art. 33, VIII como hipótese de transferência)*

**Variante, caso a equipe mantenha o consentimento como base da finalidade essencial:** trocar a primeira caixa por "☐ **Autorizo** o tratamento do meu nome, e-mail, fotos das peças, histórico de looks e avaliações para as finalidades descritas acima. Sei que posso revogar esta autorização a qualquer momento em Perfil e que, sem ela, não é possível usar o app." — e definir no aviso o prazo de eliminação após a revogação.

**Itens que só cabem na segunda camada (aviso completo):** tabela dado × finalidade × base legal × prazo; lista de suboperadores; hipótese de transferência internacional; medidas de segurança em linguagem simples; procedimento em caso de incidente; como é feita a personalização (pesos de preferência) e como zerá-la; procedimento se for identificada conta de menor de 18 anos.

### Gaps
- Colchetes dependem de decisões pendentes: controlador, contato/encarregado, região do Supabase, data de encerramento, prazo de backup, hipótese de transferência.
- Se houver submissão a comitê de ética, o TCLE é documento distinto e pode exigir conteúdo adicional (riscos, benefícios, voluntariedade) — não pesquisado.
- Minuta não revisada por profissional do Direito.
