# Barra de qualidade e práticas de implementação para o frontend PWA mobile-first do StyleUp (React 18 + TS + Vite 6 + vite-plugin-pwa + Supabase) — estado em novembro/2026

Convenções destas notas:
- "Cited Findings" = fatos lidos diretamente na fonte indicada durante esta pesquisa (14/11/2026).
- "Inferences" = síntese/recomendação minha. Quando um item depende de conhecimento prévio NÃO reverificado nesta pesquisa, está marcado com **[não verificado]**.
- As razões de contraste foram calculadas por script (fórmula de luminância relativa da WCAG), não copiadas de terceiros.

---

## 1. Acessibilidade (WCAG 2.2 AA) aplicada à UI mobile do StyleUp

### Takeaway
A paleta proposta passa em AA para texto principal, texto secundário (por margem mínima: 4,65:1) e botão primário, mas **branco sobre #A9A892 reprova (2,41:1)** e #A9A892 também não serve como contorno/ícone sobre o creme (2,08:1). Os critérios que mais afetam o redesenho são 1.4.1 (nome da cor em texto), 1.4.3/1.4.11 (contraste), 2.5.8 (alvo ≥ 24×24 CSS px; mirar 44–48), 2.4.11 (foco não coberto pela tab bar fixa), 2.5.7 (alternativa a arrastar/swipe), 3.3.8 (login sem teste cognitivo) e 4.1.3 (status assíncrono anunciado sem mover foco).

### Cited Findings

**Razões de contraste calculadas (fórmula WCAG: (L1+0,05)/(L2+0,05), sRGB linearizado)** — definição da fórmula em [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

| Par (frente sobre fundo) | Razão | Texto normal AA (4,5) | Texto grande AA / não-texto (3,0) | AAA texto (7,0) |
|---|---|---|---|---|
| #1F1F1B sobre #F2EEE3 (texto principal) | **14,26:1** | passa | passa | passa |
| #6B6B60 sobre #F2EEE3 (texto secundário) | **4,65:1** | passa (margem de 0,15) | passa | reprova |
| #FFFFFF sobre #4A5233 (botão primário) | **8,25:1** | passa | passa | passa |
| #FFFFFF sobre #6B7340 (oliva médio) | **5,06:1** | passa | passa | reprova |
| #FFFFFF sobre #A9A892 (oliva-acinzentado claro) | **2,41:1** | **reprova** | **reprova** | reprova |
| #4A5233 sobre #F2EEE3 (oliva como texto/ícone) | **7,12:1** | passa | passa | passa |

Pares extras calculados (úteis para tokens):

| Par | Razão | Observação |
|---|---|---|
| #6B6B60 sobre #FFFFFF (texto secundário em card branco) | 5,39:1 | passa AA |
| #4A5233 sobre #FFFFFF | 8,25:1 | passa AA/AAA |
| #6B7340 sobre #F2EEE3 | 4,36:1 | reprova texto normal; serve para texto grande/ícone/borda |
| #A9A892 sobre #F2EEE3 | 2,08:1 | reprova 3:1 → não usar como única borda de input/chip nem como ícone informativo |
| #1F1F1B sobre #A9A892 | 6,85:1 | texto escuro sobre o tom claro passa AA |
| #8A8A7A sobre #F2EEE3 | 3,02:1 | tom mais claro que ainda atinge 3:1 (limite) para bordas/ícones |
| #8C8B76 sobre #F2EEE3 | 2,98:1 | já reprova 3:1 |
| #FFFFFF sobre #74735F | 4,82:1 | fundo "desabilitado-mas-legível" mais claro que ainda aceita texto branco |
| #FFFFFF sobre #7A7964 | 4,42:1 | reprova 4,5 |
| #E3DDCB sobre #F2EEE3 | 1,17:1 | só para divisores decorativos |

**Critérios normativos (texto da recomendação W3C)**
- 1.4.3 Contraste (Mínimo), AA: exige-se 4,5:1 para texto e imagens de texto; texto em escala grande cai para 3:1; "escala grande" é definida como ao menos 18 pt, ou 14 pt em negrito — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.4.11 Contraste Não-textual, AA: componentes de interface e objetos gráficos necessários à compreensão precisam de 3:1 contra as cores adjacentes — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.4.1 Uso de Cor, nível A: nenhuma informação ou ação pode depender apenas de cor como meio visual — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.4.4 Redimensionar texto, AA: o conteúdo deve aguentar zoom de texto até 200% sem perda de conteúdo/função — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.4.10 Reflow, AA: sem rolagem em duas dimensões a 320 CSS px de largura (conteúdo de rolagem vertical) ou 256 CSS px de altura, salvo conteúdo que precise de layout 2D — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.4.12 Espaçamento de texto, AA: o layout não pode quebrar quando o usuário aplica altura de linha 1,5×, espaçamento de parágrafo 2×, letter-spacing 0,12× e word-spacing 0,16× o tamanho da fonte — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.3.4 Orientação, AA: travar a app em retrato só é aceitável se a orientação for essencial — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 1.3.5 Identificar propósito do input, AA: campos que coletam dados do usuário devem ter propósito determinável por programa (na prática, `autocomplete`) — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.4.7 Foco Visível, AA: qualquer UI operável por teclado precisa de indicador de foco visível — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.4.11 Foco Não Obscurecido (Mínimo), AA (novo na 2.2): o componente focado não pode ficar totalmente escondido por conteúdo criado pelo autor — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.5.7 Movimentos de Arrastar, AA (novo): toda função feita por arraste precisa de alternativa com ponteiro único sem arrastar, exceto quando o arraste é essencial ou é comportamento do user agent não modificado — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.5.8 Tamanho do Alvo (Mínimo), AA (novo): alvos de ponteiro com no mínimo 24×24 CSS px; exceções: espaçamento (círculo de 24 px centrado no alvo menor não intersecta outro alvo), controle equivalente na página, alvo inline em frase, controle do user agent, apresentação essencial — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.5.5 Tamanho do Alvo (Aprimorado), AAA: 44×44 CSS px — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.3.3 Animação por Interações é AAA (não AA): animação de movimento disparada por interação deve poder ser desativada, salvo se essencial — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 2.2.1 Tempo Ajustável, A: limites de tempo impostos pelo conteúdo precisam poder ser desligados, ajustados (≥ 10× o padrão) ou estendidos — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 3.3.1 Identificação de Erro, A: erro detectado automaticamente → item identificado e erro descrito em texto; 3.3.3 Sugestão de Erro, AA: fornecer a correção quando conhecida — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 3.3.7 Entrada Redundante, A (novo): informação já fornecida no mesmo processo deve vir preenchida ou selecionável — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 3.3.8 Autenticação Acessível (Mínimo), AA (novo): nenhum passo de autenticação pode exigir teste de função cognitiva, a menos que haja método alternativo, mecanismo de auxílio, reconhecimento de objetos ou identificação de conteúdo pessoal fornecido pelo usuário — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 3.2.6 Ajuda Consistente, A (novo): mecanismos de ajuda repetidos em várias páginas mantêm a mesma ordem relativa — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 4.1.2 Nome, Função, Valor, A: todo componente precisa de nome e role determináveis por programa; estados e valores expostos a tecnologias assistivas — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- 4.1.3 Mensagens de Status, AA: mensagens de status devem ser determináveis por programa para serem anunciadas sem receber foco — [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

**Diálogos / bottom sheets (padrão ARIA APG)**
- O contêiner do modal leva `role="dialog"` + `aria-modal="true"` e um nome acessível via `aria-labelledby` (título visível) ou `aria-label`; `aria-describedby` é opcional e deve ser omitido quando o conteúdo tem estrutura (listas, vários parágrafos) — [ARIA APG: Modal Dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- Teclado: Tab/Shift+Tab circulam apenas dentro do diálogo (focus trap) e Escape fecha — [ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- Foco inicial: por padrão no primeiro elemento focável; em ações irreversíveis (ex.: excluir dados) o APG sugere focar a ação menos destrutiva; ao fechar, o foco volta ao elemento que abriu — [ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- O conteúdo atrás do modal deve ficar inerte e visualmente esmaecido; o APG recomenda fortemente um botão visível de fechar/cancelar na ordem de tabulação — [ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

**Mensagens de erro e cor**
- A NN/g orienta posicionar o erro junto ao campo causador e nunca sinalizar erro só por cor ou animação, porque muitos usuários têm deficiência de visão de cores — [NN/g Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)

**Movimento**
- Skeletons animados (pulso/shimmer) podem distrair ou causar problemas de acessibilidade para parte dos usuários, segundo a NN/g — [NN/g Skeleton Screens](https://www.nngroup.com/articles/skeleton-screens/)
- O Playwright consegue emular `reducedMotion: 'reduce'`, `forcedColors: 'active'` e `contrast: 'more'` via config ou `page.emulateMedia()` para testar essas preferências — [Playwright Emulation](https://playwright.dev/docs/emulation)

### Inferences
- **Tokens de cor recomendados a partir dos cálculos**: texto principal #1F1F1B; texto secundário #6B6B60 só sobre creme/branco e nunca abaixo desse tom (para folga, #62625A dá 5,31:1 e #5E5E54 dá 5,65:1 sobre o creme); botão primário #4A5233 com texto branco (8,25:1) ou creme (#F2EEE3 sobre #4A5233 = 7,12:1); #6B7340 aceita texto branco (5,06:1) mas não serve como cor de texto normal sobre o creme (4,36:1); **#A9A892 só como superfície decorativa ou com texto escuro #1F1F1B (6,85:1)** — nunca com texto branco, nem como borda única de chip/input (2,08:1). Para borda/ícone informativo sobre o creme, usar tom igual ou mais escuro que #8A8A7A (3,02:1).
- Conversão prática de "texto grande": 18 pt ≈ 24 CSS px e 14 pt bold ≈ 18,66 CSS px bold (1 pt = 1,333 px). Rótulos de 12–14 px da tab bar e dos chips são "texto normal" → exigem 4,5:1.
- Estado desabilitado: a WCAG isenta de contraste componentes inativos (1.4.3 e 1.4.11), mas um botão "Salvar" que apenas *parece* desabilitado (#A9A892 + branco) enquanto está ativo reprova. Preferir manter o botão ativo e validar no clique, ou usar `aria-disabled="true"` com texto escuro.
- **Cor nunca sozinha (requisito do produto + SC 1.4.1)**: em cada peça mostrar o NOME da cor em texto (ex.: "Verde-oliva") ao lado/abaixo do swatch; filtros de cor = chip com swatch + rótulo; chip selecionado deve mudar algo além da cor (ícone de check, borda mais grossa, `aria-pressed="true"`); erros com ícone + texto; like/dislike com ícones distintos e não só verde/vermelho.
- **Alvos de toque**: 24×24 CSS px é o piso legal (AA); adotar 44×44 CSS px como padrão interno (coincide com AAA 2.5.5) e 48×48 para a tab bar e botões principais. Os valores 44×44 pt (iOS) e 48 dp (Android) citados no briefing são a orientação de plataforma usual **[não verificado nesta pesquisa]**. Com 5 abas em 390 px, cada aba tem 78 px de largura — suficiente.
- **Tab bar**: `<nav aria-label="Navegação principal">` contendo links (`<a>`/`NavLink`), o item ativo com `aria-current="page"`; rótulo de texto sempre visível (também exigido por HIG, ver seção 6); ícones com `aria-hidden="true"` quando há rótulo. Não usar `role="tablist"` (isso é para abas que trocam painéis na mesma página, não para navegação entre rotas) **[não verificado]**.
- **2.4.11 com tab bar fixa**: aplicar `scroll-padding-bottom: calc(<altura da tab bar> + env(safe-area-inset-bottom))` no contêiner de rolagem e `padding-bottom` equivalente no conteúdo, para que um campo/botão focado nunca fique totalmente atrás da barra ou de um CTA fixo ("Salvar look").
- **2.5.7**: qualquer swipe (curtir/descartar look, carrossel da faixa de peças, reordenar peças do collage) precisa de botões equivalentes ("Gerar outro", "Salvar", setas). Para temperatura, `<input type="range">` nativo (com `aria-valuetext="22 °C"`) ou stepper +/−; evitar slider custom só por arraste.
- **3.3.8**: não bloquear colar no campo de senha; usar `autocomplete="email"`, `current-password`, `new-password` (também atende 1.3.5); botão "mostrar senha"; não usar CAPTCHA de quebra-cabeça sem alternativa. Link mágico/OTP por e-mail contam como alternativa.
- **Botões só com ícone** (voltar, fechar, câmera, favoritar, excluir): `aria-label` em pt-BR descrevendo a ação ("Excluir peça Camisa branca"), ícone `aria-hidden`. O rótulo visível deve estar contido no nome acessível (SC 2.5.3) **[não verificado nesta pesquisa]**.
- **Live regions (4.1.3)**: manter um `<div role="status" aria-live="polite">` montado desde o início e trocar o texto ("Analisando foto…", "Look gerado", "Peça salva"); erros bloqueantes com `role="alert"`. Não mover o foco para toasts.
- **Bottom sheet/diálogo**: preferir `<dialog>` + `showModal()` (torna o resto inerte e trata Escape nativamente) ou, em sheet custom, atributo `inert` no `#root` irmão **[suporte de navegadores não reverificado]**; no diálogo de exclusão de conta, foco inicial em "Cancelar".
- **Movimento reduzido**: mesmo sendo AAA (2.3.3), respeitar `@media (prefers-reduced-motion: reduce)` desligando shimmer, transições de página e animação do splash; é barato e testável no Playwright.
- **Zoom/reflow**: nunca usar `user-scalable=no`/`maximum-scale=1`; tamanhos de fonte em `rem`; testar a 320 px de largura e com zoom de texto 200% (chips devem quebrar linha, tab bar não pode truncar rótulos).
- **Orientação**: o manifest pode sugerir retrato, mas o layout deve continuar utilizável em paisagem (1.3.4); no iOS o campo `orientation` do manifest nem é suportado (ver seção 2).

### Gaps
- Não reli os documentos "Understanding" de cada SC (ex.: detalhes de quando senha conta como teste cognitivo em 3.3.8, ou os estados de 1.4.11); as notas acima usam o texto normativo.
- 2.4.13 Focus Appearance (AAA) e 2.5.3 Label in Name não vieram no trecho extraído da recomendação.
- Não verifiquei nesta pesquisa as páginas da Apple/Material com os números 44 pt/48 dp nem a tabela de suporte atual de `inert` e `<dialog>` no iOS Safari.

---

## 2. PWA no fim de 2026 com vite-plugin-pwa/Workbox

### Takeaway
Instalabilidade no Chrome exige apenas manifest correto (nome, ícones 192+512, `start_url`, `display`) + HTTPS + engajamento mínimo — service worker não é mais critério; no iOS a instalação é sempre manual (menu Compartilhar), sem `beforeinstallprompt`, e desde o iOS 26 todo site adicionado à Tela de Início abre como web app. Para o StyleUp, o ponto crítico é o cache de imagens com URL assinada (cada token é uma chave de cache distinta) e a escolha `prompt` em vez de `autoUpdate`, pois a app tem formulários.

### Cited Findings

**Instalabilidade — Chrome/Android**
- Critérios do Chrome para disparar `beforeinstallprompt` (página atualizada em 19/09/2024): app ainda não instalada; usuário clicou/tocou ao menos uma vez e ficou ao menos 30 s na página; HTTPS; manifest com `short_name` ou `name`, `icons` contendo 192 px e 512 px, `start_url`, `display` em `fullscreen`/`standalone`/`minimal-ui`/`window-controls-overlay`, e `prefer_related_applications` ausente ou `false`. A lista não inclui service worker — [web.dev install criteria](https://web.dev/articles/install-criteria)
- O MDN confirma que service worker não é requisito de instalação e que os mesmos membros do manifest valem para Chrome, Edge e Samsung Internet; em desenvolvimento `localhost`/`127.0.0.1` substituem HTTPS — [MDN Making PWAs installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- No Android, WebAPK "de verdade" (entrada no launcher e no alternador de apps) só sai pelo Chrome em aparelhos com Google Mobile Services e pelo Samsung Internet; Firefox, Edge, Opera e Chrome sem GMS criam apenas atalho com selo do navegador — [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- `description` e `screenshots` do manifest aparecem no diálogo de instalação somente no Android — [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- Firefox desktop não instala PWAs via manifest — [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)

**Instalabilidade — iOS/iPadOS** (fonte principal: tabela de compatibilidade de Maximiliano Firtman, atualizada em 13/10/2026)
- A partir do iOS 16.4 a instalação pode ser feita pelo menu Compartilhar em Safari, Chrome, Edge, Firefox ou Orion; até 16.3 só no Safari — [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- `beforeinstallprompt` e banners de instalação não existem no iOS — [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable); [firt.dev](https://firt.dev/notes/pwa-ios/)
- Desde o iOS 26.0 qualquer site pode ser instalado e abre como web app por padrão, mesmo sem manifest nem a meta `apple-mobile-web-app-capable` (o usuário pode optar por favorito comum) — [firt.dev](https://firt.dev/notes/pwa-ios/)
- Ícones do manifest só passaram a valer no iOS 15.4; se existir `<link rel="apple-touch-icon">`, ele se sobrepõe aos ícones do manifest; SVG no manifest funciona desde 26.0, mas não no link apple-touch-icon — [firt.dev](https://firt.dev/notes/pwa-ios/)
- `theme_color` do manifest é suportado desde 15.0; `display` aceita apenas `browser` e `standalone` (`minimal-ui`/`fullscreen` caem em fallback); `background_color` e `orientation` não são suportados — [firt.dev](https://firt.dev/notes/pwa-ios/)
- Splash screen no iOS continua dependendo de `apple-touch-startup-image`, que só funciona com a meta `apple-mobile-web-app-capable` presente — [firt.dev](https://firt.dev/notes/pwa-ios/)
- A meta `apple-mobile-web-app-status-bar-style` está depreciada desde 15.0 em favor da meta `theme-color`, porém `black-translucent` segue sendo o único jeito de obter app em tela cheia (conteúdo sob a status bar) — [firt.dev](https://firt.dev/notes/pwa-ios/)
- Web Push (16.4+), Notifications e App Badging funcionam só para web apps instaladas; Background Sync, Periodic Background Sync e Background Fetch não são suportados; Screen Wake Lock para apps instaladas veio na 18.4 — [firt.dev](https://firt.dev/notes/pwa-ios/)
- Detecção de modo instalado: `navigator.standalone` foi superado pela media query `display-mode` — [firt.dev](https://firt.dev/notes/pwa-ios/)

**Safe areas**
- Layout de borda a borda requer `viewport-fit=cover` na meta viewport (`<meta name="viewport" content="initial-scale=1, viewport-fit=cover">`); o padrão é `auto` — [WebKit: Designing Websites for iPhone X](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)
- As quatro variáveis `env(safe-area-inset-top|right|bottom|left)` podem valer 0, por isso o WebKit recomenda combiná-las com `max()` (ex.: `padding-left: max(12px, env(safe-area-inset-left))`) — [WebKit](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)

**Armazenamento no Safari**
- Desde o Safari 17, cada origem pode usar até 60% do disco em apps-navegador e 15% em outros apps; web apps de Tela de Início recebem as mesmas cotas de um app-navegador; estourar a cota lança `QuotaExceededError` — [WebKit: Updates to Storage Policy](https://webkit.org/blog/14403/updates-to-storage-policy/)
- A remoção automática de dados pode ocorrer por cota geral excedida, pressão de armazenamento do sistema ou ausência de interação do usuário por "algum tempo" (ITP), em ordem LRU por origem; origens em modo persistente podem ser poupadas e `navigator.storage.persist()` é concedido por heurística — [WebKit](https://webkit.org/blog/14403/updates-to-storage-policy/)

**vite-plugin-pwa — fluxo de atualização**
- Com `registerType: 'autoUpdate'` o plugin força `workbox.clientsClaim` e `workbox.skipWaiting` para `true` e recarrega as abas abertas quando há nova versão; a documentação alerta para perda de dados em formulários não salvos, recomenda `prompt` para apps com formulários e avisa que migrar de `autoUpdate` para `prompt` depois é difícil — [vite-pwa: Automatic reload](https://vite-pwa-org.netlify.app/guide/auto-update.html)
- `prompt` é o valor padrão de `registerType`; o registro usa `registerSW({ onNeedRefresh(){}, onOfflineReady(){} })` de `virtual:pwa-register`, e chamar a função retornada (`updateSW()`) recarrega com o conteúdo novo — [vite-pwa: Prompt for update](https://vite-pwa-org.netlify.app/guide/prompt-for-update.html)
- `workbox.cleanupOutdatedCaches` já vem ativo na estratégia `generateSW` e a doc pede fortemente para não desligar — [vite-pwa](https://vite-pwa-org.netlify.app/guide/prompt-for-update.html)

**Workbox — estratégias e plugins**
- `StaleWhileRevalidate` responde do cache e revalida na rede a cada requisição (indicado quando a versão mais nova não é crítica); `NetworkFirst` tenta rede e cai no cache em falha (indicado para dados que mudam muito); `CacheFirst` serve para assets versionados; `NetworkOnly` para o que precisa vir sempre da rede — [Workbox strategies](https://developer.chrome.com/docs/workbox/modules/workbox-strategies)
- `NetworkFirst` e `StaleWhileRevalidate` guardam por padrão respostas 200 **e respostas opacas** (cross-origin sem CORS) — [Workbox strategies](https://developer.chrome.com/docs/workbox/modules/workbox-strategies)
- O callback de plugin `cacheKeyWillBeUsed({request, mode, params, event, state})` roda antes de leitura (`mode: 'read'`) e escrita (`'write'`) e pode devolver uma string ou `Request` cuja URL vira a chave de cache — é o ponto oficial para normalizar URLs — [Workbox plugins](https://developer.chrome.com/docs/workbox/using-plugins)
- `cacheWillUpdate` pode retornar `null` para impedir que uma resposta entre no cache; `handlerDidError` permite devolver uma `Response` de fallback quando rede e cache falham; `fetchDidFail` só dispara em falha de rede, não em HTTP 4xx/5xx — [Workbox plugins](https://developer.chrome.com/docs/workbox/using-plugins)
- Exemplo oficial de cache de imagens: `CacheFirst` + `ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30*24*60*60 })` — [Workbox plugins](https://developer.chrome.com/docs/workbox/using-plugins)

**URLs assinadas do Supabase e cache**
- O CDN do Supabase trata cada token distinto como chave de cache separada: duas URLs assinadas do mesmo objeto são cacheadas separadamente e a primeira requisição de uma URL nova é sempre miss — [Supabase Smart CDN](https://supabase.com/docs/guides/storage/cdn/smart-cdn)
- `cacheControl` no upload define por quanto tempo o navegador guarda o asset; o TTL padrão de navegador é tipicamente 1 hora; Smart CDN é ativado automaticamente só em planos Pro ou superiores — [Supabase Smart CDN](https://supabase.com/docs/guides/storage/cdn/smart-cdn)

### Inferences
- **Manifest sugerido** (via opção `manifest` do VitePWA): `name: "StyleUp"`, `short_name: "StyleUp"`, `lang: "pt-BR"`, `start_url: "/"`, `scope: "/"`, `id: "/"`, `display: "standalone"`, `theme_color: "#F2EEE3"`, `background_color: "#F2EEE3"`, ícones PNG 192 e 512 (`purpose: "any"`) + um 512 `purpose: "maskable"` com a arte dentro da zona segura central **[purpose maskable/zona segura de 80% não reverificados nesta pesquisa]**, `description` e `screenshots` (melhoram o diálogo no Android).
- **`index.html`**: `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`; `<meta name="theme-color" content="#F2EEE3">`; `<link rel="apple-touch-icon" href="/apple-touch-icon-180.png">` (PNG opaco 180×180 — como ele se sobrepõe aos ícones do manifest no iOS, precisa existir com boa qualidade; tamanho 180 **[não verificado]**); opcional `apple-mobile-web-app-capable` + `apple-touch-startup-image` se quiser splash nativo no iOS.
- **CSS de safe area**: tab bar com `padding-bottom: max(8px, env(safe-area-inset-bottom))`; cabeçalho com `padding-top: env(safe-area-inset-top)`; altura útil com `100dvh` em vez de `100vh`.
- **Install UX**: no Android capturar `beforeinstallprompt`, `preventDefault()` e oferecer botão "Instalar app" no Perfil/Home depois de um momento de valor (ex.: após salvar o 1º look). No iOS mostrar instrução ilustrada ("Compartilhar → Adicionar à Tela de Início") apenas quando `!matchMedia('(display-mode: standalone)').matches` e o UA for iOS.
- **Atualização**: usar `registerType: 'prompt'` (app tem formulários de cadastro, prompt livre, confirmação de foto). Mostrar toast "Nova versão disponível — Atualizar". No React existe o hook `useRegisterSW` em `virtual:pwa-register/react` (retorna `needRefresh`, `offlineReady`, `updateServiceWorker`) **[não verificado nesta pesquisa]**. Checar update periodicamente (ex.: a cada 60 min via `registration.update()`), pois PWA instalada pode ficar dias aberta.
- **Estratégia de cache proposta**:
  1. App shell (JS/CSS/HTML/fontes/ícones): precache do Workbox (`globPatterns: ['**/*.{js,css,html,woff2,svg,png}']`) + `navigateFallback: '/index.html'` com `navigateFallbackDenylist: [/^\/api\//]`.
  2. **API autenticada (FastAPI)**: padrão `NetworkOnly` (ou simplesmente não registrar rota) para tudo que carrega `Authorization`. Se quiser leitura offline do guarda-roupa, guardar os dados no cliente por usuário (ex.: TanStack Query persistido em IndexedDB com chave que inclui `user.id`) em vez de cachear respostas HTTP no SW. Se ainda assim usar `NetworkFirst` (ex.: `networkTimeoutSeconds: 3`) para GETs, usar `cacheName` exclusivo e **apagar no logout** (`caches.delete('api-user')` ao receber `SIGNED_OUT`), pois o Cache Storage não é particionado por usuário e o Workbox não respeita `Authorization` nem varia a chave por token.
  3. **Imagens de URL assinada**: `CacheFirst` com `cacheKeyWillBeUsed` removendo o parâmetro `token` (chave = origem + caminho do objeto [+ parâmetros de transformação]); `CacheableResponsePlugin({ statuses: [200] })` (não cachear opacas — exigir CORS com `crossorigin="anonymous"` nas `<img>`); `ExpirationPlugin({ maxEntries: ~300, maxAgeSeconds: 30 dias, purgeOnQuotaError: true })`. Como o caminho do objeto no bucket inclui o id do usuário, a chave já é separada por usuário; ainda assim limpar esse cache no logout em aparelho compartilhado.
  4. Alternativa/adição sem SW: assinar em lote com validade longa e **reutilizar a mesma URL** enquanto válida (cache em memória/IndexedDB de `{path → signedUrl, expiresAt}`), o que faz o cache HTTP do navegador e o CDN acertarem.
- Esboço de rota (modo `injectManifest`, mais seguro para lógica custom; no `generateSW` as funções de plugin são serializadas e não podem usar closures **[não verificado]**):
  ```ts
  registerRoute(
    ({ url }) => url.hostname.endsWith('.supabase.co') && url.pathname.startsWith('/storage/v1/object/sign/'),
    new CacheFirst({
      cacheName: 'wardrobe-images',
      plugins: [
        { cacheKeyWillBeUsed: async ({ request }) => { const u = new URL(request.url); u.searchParams.delete('token'); return u.href; } },
        new CacheableResponsePlugin({ statuses: [200] }),
        new ExpirationPlugin({ maxEntries: 300, maxAgeSeconds: 30 * 24 * 3600, purgeOnQuotaError: true }),
      ],
    }),
  );
  ```
  Risco a aceitar conscientemente: a imagem continua legível offline no aparelho depois que o token expira (mesmo comportamento que o próprio CDN do Supabase tem — ver seção 3); mitigação = limpar cache em `SIGNED_OUT` e na exclusão de conta/peça.
- **Offline fallback**: como é SPA, `navigateFallback` já serve o shell; cada tela precisa de estado "Sem conexão" (com `navigator.onLine` + falha de fetch) e botão "Tentar de novo"; geração de look e análise de foto são online-only — desabilitar com explicação textual.
- **iOS**: pedir `navigator.storage.persist()` após login para reduzir risco de evicção; não depender de Background Sync para uploads (não existe no iOS) — fazer fila em memória/IndexedDB e reenviar quando a app voltar ao primeiro plano.

### Gaps
- Não encontrei, nesta pesquisa, documentação oficial do Supabase ou do Workbox descrevendo explicitamente o padrão "remover `token` na chave de cache"; a recomendação é derivada da API `cacheKeyWillBeUsed` + comportamento de cache por token.
- Regra dos "7 dias" de evicção de storage do Safari/ITP e sua isenção para apps instaladas: a página do WebKit lida só fala em "algum tempo" sem número; não confirmei o valor.
- Tamanhos exatos recomendados para `apple-touch-icon` e especificação de zona segura de ícone maskable não foram verificados em fonte primária aqui.
- Não verifiquei o estado da categoria PWA do Lighthouse em 2026 (ver seção 8).
- Não verifiquei mudanças do Chrome posteriores a 09/2024 nos critérios de instalação (a página web.dev lida tem essa data).

---

## 3. Supabase JS v2: URLs assinadas, transformação de imagem e Auth

### Takeaway
`createSignedUrls` assina vários caminhos numa chamada (expiração em segundos); transformação de imagem **não existe no plano Free** (Pro+), então thumbnails precisam ser gerados no cliente ou no FastAPI. O deadlock clássico de `onAuthStateChange` foi atenuado pelo modo "lockless" do auth-js recente, mas a prática segura continua sendo callback síncrono e trabalho adiado.

### Cited Findings

**Storage**
- `createSignedUrls(paths, expiresIn, options?)` recebe um array de caminhos (ex.: `['folder/image.png', 'folder2/image2.png']`) e `expiresIn` em segundos; retorna `{ data, error }` — [Supabase JS: createSignedUrls](https://supabase.com/docs/reference/javascript/storage-from-createsignedurls)
- `createSignedUrl(path, expiresIn, options?)` aceita `options.transform` (ex.: `{ width: 100, height: 100 }`) e `options.download: true` — [Supabase JS: createSignedUrl](https://supabase.com/docs/reference/javascript/storage-from-createsignedurl)
- Redimensionamento de imagem está habilitado apenas para plano Pro e superiores; limites: largura/altura de 1 a 2500, arquivo até 25 MB, resolução até 50 MP, `quality` 20–100 (padrão 80), modos `cover` (padrão)/`contain`/`fill` — [Supabase Image Transformations](https://supabase.com/docs/guides/storage/serving/image-transformations)
- HEIC é aceito pelo serviço de transformação apenas como formato de origem; a otimização automática de formato hoje entrega WebP (AVIF planejado) e `format=origin` mantém o original — [Supabase Image Transformations](https://supabase.com/docs/guides/storage/serving/image-transformations)
- Preço: Pro/Team incluem 100 imagens de origem por ciclo; excedente a US$ 5 por 1.000 imagens de origem — [Supabase Image Transformations](https://supabase.com/docs/guides/storage/serving/image-transformations)
- Em URL assinada, as opções de `transform` ficam embutidas no token e não podem ser alteradas depois — [Supabase Image Transformations](https://supabase.com/docs/guides/storage/serving/image-transformations)
- Revogar/expirar um token não purga a entrada do CDN: a resposta em cache pode continuar sendo servida após a expiração até acabar o TTL do CDN; para cortar acesso é preciso apagar o objeto, e a invalidação leva até 60 segundos — [Supabase Smart CDN](https://supabase.com/docs/guides/storage/cdn/smart-cdn)
- Para assets que podem ser apagados, a doc recomenda TTL de navegador mais curto via `cacheControl`; para assets atualizados com frequência, subir em novo caminho — [Supabase Smart CDN](https://supabase.com/docs/guides/storage/cdn/smart-cdn)

**Auth — `onAuthStateChange`**
- A referência lista os eventos `INITIAL_SESSION`, `SIGNED_IN`, `SIGNED_OUT`, `PASSWORD_RECOVERY`, `TOKEN_REFRESHED`, `USER_UPDATED`, e o cancelamento por `data.subscription.unsubscribe()` (no React, no cleanup do `useEffect`) — [Supabase JS: onAuthStateChange](https://supabase.com/docs/reference/javascript/auth-onauthstatechange)
- A doc de troubleshooting do Supabase reconhece um bug: chamada assíncrona à API dentro do handler de `onAuthStateChange` causa deadlock, e as chamadas seguintes pelo mesmo client ficam penduradas — [Supabase Troubleshooting](https://supabase.com/docs/guides/troubleshooting/why-is-my-supabase-api-call-not-returning-PGzXw0)
- Causa explicada por mantenedor: um lock adicionado para evitar reuso de refresh token; o callback segura o lock enquanto aguarda uma requisição que precisa do mesmo lock. Contorno difundido: não marcar o callback como `async`, não dar `await` em chamadas Supabase dentro dele e adiar o trabalho com `setTimeout(() => {...}, 0)`; manter uma única assinatura na app — [auth-js issue #762](https://github.com/supabase/auth-js/issues/762)
- O pacote `@supabase/auth-js@2.110.0` traz um guia de migração dizendo que a coordenação padrão passou a ser sem lock (sem `navigator.locks`); callbacks assíncronos que chamam `getUser`, `setSession` ou leem a sessão ficaram seguros no caminho padrão; **permanece** o deadlock ao chamar `refreshSession` dentro de um handler de `TOKEN_REFRESHED`; opções `lock`/`lockAcquireTimeout` estão depreciadas e serão removidas na v3; recomenda chamar `client.auth.dispose()` em cleanup (React Strict Mode/HMR) — [auth-js lockless-coordination.md](https://cdn.jsdelivr.net/npm/@supabase/auth-js@2.110.0/migrations/lockless-coordination.md)
- Esse mesmo guia tem o campo de versão como placeholder ("Since: v2.X.Y") e menciona mudança de comportamento por volta da v2.107, portanto a versão exata de introdução não está explícita — [auth-js lockless-coordination.md](https://cdn.jsdelivr.net/npm/@supabase/auth-js@2.110.0/migrations/lockless-coordination.md)

**Auth — cadastro e senha**
- Confirmação de e-mail vem ligada por padrão em projetos hospedados; `options.emailRedirectTo` define o destino do link e precisa constar em Redirect URLs; sem ele o usuário vai para a Site URL, cujo padrão é `localhost:3000` — [Supabase Password-based Auth](https://supabase.com/docs/guides/auth/passwords)
- `resetPasswordForEmail(email, { redirectTo })` não revela se a conta existe (retorna sem erro mesmo sem usuário); a página de troca de senha chama `supabase.auth.updateUser({ password })` com o usuário já em sessão — [Supabase Password-based Auth](https://supabase.com/docs/guides/auth/passwords)
- Desde o supabase-js v2.102.0, `updateUser` aceita `current_password` para exigir a senha atual — [Supabase Password-based Auth](https://supabase.com/docs/guides/auth/passwords)
- Fluxo padrão no JavaScript é o implícito (token entregue direto ao site); PKCE é o indicado para SSR e usa troca de token (`verifyOtp` com `token_hash`) — [Supabase Password-based Auth](https://supabase.com/docs/guides/auth/passwords)
- O serviço de e-mail embutido limita a 2 e-mails por hora e é "best-effort"; produção exige SMTP próprio — [Supabase Password-based Auth](https://supabase.com/docs/guides/auth/passwords)

### Inferences
- **Sem transformação no Free → gerar derivados no upload**: o cliente (ou o FastAPI, que já processa a foto) deve gravar 2 objetos por peça — `display` (~1024–1280 px) e `thumb` (~384–512 px) — e a grade assina só os thumbs. Isso também reduz egress.
- **Padrão de assinatura**: um único `createSignedUrls(paths, 3600…86400)` por página da grade (não N chamadas); guardar `{path, signedUrl, expiresAt}` num cache (TanStack Query com `staleTime` ≈ 80% da validade) e reassinar antes de expirar; nunca persistir URLs assinadas em `localStorage` além da validade. Validade sugerida: 1 h para dados sensíveis e alto giro; até 24 h para thumbs se o risco de link vazado for aceitável (decisão de privacidade/LGPD — a URL assinada é um "bearer link").
- **Exclusão (LGPD)**: como URLs expiradas podem seguir servidas pelo CDN e pelo cache do SW, a exclusão de peça/conta deve **apagar o objeto** no bucket (não basta esperar expirar) e limpar `caches` locais.
- **Padrão seguro para `onAuthStateChange` em React 18**: registrar uma única vez (fora de componentes ou em provider), callback síncrono que só faz `setSession(session)`/`queryClient.clear()` e agenda efeitos com `setTimeout(..., 0)`; buscar perfil em `useEffect` dependente de `session?.user.id`. Mesmo com o modo lockless, manter esse padrão evita depender da versão exata do auth-js. Em StrictMode o efeito roda duas vezes → sempre `unsubscribe()` no cleanup.
- **Evento `PASSWORD_RECOVERY`**: na rota de `redirectTo`, ao receber esse evento exibir o formulário de nova senha e então `updateUser({ password })`.
- **`signUp` com confirmação**: tratar o retorno sem sessão como "verifique seu e-mail" e usar mensagem neutra para e-mail já cadastrado (evita enumeração de contas) **[comportamento exato do retorno de `signUp` para e-mail existente não verificado nesta pesquisa]**.
- Configurar SMTP próprio antes de qualquer teste com usuários reais (limite de 2 e-mails/h inviabiliza cadastro + reset).

### Gaps
- A referência JS não documenta, nas páginas lidas, o formato exato de `data` de `createSignedUrls` (campos `path`/`signedUrl`/`error` por item) nem as policies RLS necessárias (`select` em `storage.objects`); confirmar no código/tipos do `@supabase/storage-js`.
- Não encontrei recomendação oficial de valor de expiração "ideal" para URLs assinadas; os valores acima são julgamento meu.
- Não verifiquei se o plano Free tem CDN básico com o mesmo comportamento de cache por token (a página lida descreve Smart CDN, Pro+).
- A página de referência de `onAuthStateChange` lida não contém o aviso de deadlock (só a frase de que é seguro usar sem função async); a versão exata do supabase-js em que o modo lockless virou padrão ficou indeterminada.

---

## 4. Captura e upload de foto no mobile web

### Takeaway
`capture` é apenas uma dica não-Baseline; ofereça dois caminhos (câmera e galeria). Reduza no cliente antes de enviar — `createImageBitmap(file, { imageOrientation: 'from-image', resizeWidth })` com fallback para canvas — respeitando o teto de 16.777.216 px de área de canvas do iOS Safari; ~1024–1280 px no lado maior sobra para um ViT-B/32 (224 px) e para exibição.

### Cited Findings
- O atributo `capture` em `<input type="file">` aceita `user` (câmera frontal) e `environment` (traseira), é relevante quando `accept` indica imagem/vídeo/áudio, funciona melhor em dispositivos móveis e, no desktop, tende a abrir o seletor de arquivos comum; o MDN o classifica como "Limited availability" (fora do Baseline) — [MDN: capture](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/capture)
- `createImageBitmap(image, options)` aceita `Blob` (logo, `File`), `HTMLImageElement`, `HTMLCanvasElement`, `ImageData`, `OffscreenCanvas` etc.; opções: `imageOrientation` (`from-image` — padrão, aplica a orientação EXIF —, `flipY`, `none`), `resizeWidth`, `resizeHeight`, `resizeQuality` (`pixelated`/`low` padrão/`medium`/`high`), `premultiplyAlpha`, `colorSpaceConversion` — [MDN: createImageBitmap](https://developer.mozilla.org/en-US/docs/Web/API/Window/createImageBitmap)
- O MDN marca `createImageBitmap` como Baseline "widely available" desde setembro/2021, com a ressalva de que partes do recurso têm níveis de suporte variados — [MDN: createImageBitmap](https://developer.mozilla.org/en-US/docs/Web/API/Window/createImageBitmap)
- No iOS Safari a área máxima de um canvas é 16.777.216 px; acima disso o console mostra "Canvas area exceeds the maximum limit (width * height > 16777216)"; uma dimensão pode passar de 4096 desde que o produto fique abaixo do limite (ex.: 5120×3072 funciona); contorno = reduzir proporcionalmente antes de desenhar — [PQINA: Canvas area exceeds the maximum limit](https://pqina.nl/blog/canvas-area-exceeds-the-maximum-limit/)
- O serviço de transformação do Supabase aceita HEIC como origem, mas só em Pro+ — [Supabase Image Transformations](https://supabase.com/docs/guides/storage/serving/image-transformations)
- Para processos que não são carregamento de página (uploads, conversões), a NN/g recomenda barra de progresso ou passo-a-passo em vez de skeleton — [NN/g Skeleton Screens](https://www.nngroup.com/articles/skeleton-screens/)

### Inferences
- **Dois botões, dois inputs** (rótulos visíveis "Tirar foto" e "Escolher da galeria"): `<input type="file" accept="image/*" capture="environment">` e `<input type="file" accept="image/*">`. Em iOS e Android o `capture` costuma abrir a câmera direto, sem opção de galeria **[não verificado nesta pesquisa; MDN só diz que é dica]**; por isso a galeria precisa de input separado. Inputs visualmente ocultos mas focáveis, acionados por `<label>`/botão com nome acessível.
- **Aritmética de tamanhos**: foto de 12 MP = 4032×3024 = 12.192.768 px (cabe no limite do iOS); foto de 48 MP = 8064×6048 ≈ 48,8 M px (**estoura** o limite) → nunca desenhar o original num canvas; decodificar já reduzido (`createImageBitmap` com `resizeWidth/resizeHeight`) ou reduzir em etapas.
- **Dimensões-alvo**: classificador ViT-B/32 usa entrada de 224×224 (o pré-processamento reduz/corta para 224) **[não verificado nesta pesquisa]** → qualquer coisa ≥ 448 px já dá 2× de folga; para exibição no quadro de 390 CSS px em DPR 3 a largura cheia é 1170 px físicos e um card de grade de 2 colunas (~180 CSS px) pede ~540 px. Recomendação: enviar **1 arquivo de 1024–1280 px no lado maior**, JPEG qualidade ~0,8–0,85 (ou WebP ~0,8), alvo ≤ 300–500 KB; gerar thumb de 384–512 px.
- **Pipeline sugerido** (esboço):
  ```ts
  async function downscale(file: File, max = 1280, type = 'image/jpeg', q = 0.82): Promise<Blob> {
    let bmp: ImageBitmap;
    try {
      const probe = await createImageBitmap(file, { imageOrientation: 'from-image' });
      const s = Math.min(1, max / Math.max(probe.width, probe.height));
      const w = Math.round(probe.width * s), h = Math.round(probe.height * s);
      probe.close();
      bmp = await createImageBitmap(file, { imageOrientation: 'from-image', resizeWidth: w, resizeHeight: h, resizeQuality: 'high' });
    } catch { /* fallback: <img> + URL.createObjectURL + canvas drawImage */ throw new Error('fallback'); }
    const c = document.createElement('canvas'); c.width = bmp.width; c.height = bmp.height;
    c.getContext('2d')!.drawImage(bmp, 0, 0); bmp.close();
    const blob = await new Promise<Blob>((ok, no) => c.toBlob(b => b ? ok(b) : no(new Error('toBlob')), type, q));
    c.width = c.height = 0; // libera memória de canvas no iOS [não verificado]
    return blob;
  }
  ```
  Observações: (a) testar em iPhone real se `resizeWidth/resizeHeight` e `imageOrientation` são honrados — o MDN avisa que o suporte de partes da API varia; ter fallback `<img>` + canvas (navegadores modernos aplicam EXIF por padrão ao desenhar `<img>`) **[não verificado]**; (b) `OffscreenCanvas.convertToBlob({ type, quality })` permite fazer isso em Web Worker e não travar a UI (bom para INP), com fallback para `canvas.toBlob` **[suporte iOS não reverificado]**; (c) checar `blob.type` após `toBlob('image/webp')` — se o navegador não codifica WebP devolve PNG; JPEG é o caminho seguro.
- **HEIC**: iPhones normalmente entregam JPEG ao `<input accept="image/*">`, mas arquivos HEIC podem chegar via galeria/Arquivos **[não verificado]**; como a recompressão no cliente gera JPEG/WebP, o backend recebe formato padrão. Se `createImageBitmap` falhar na decodificação, mostrar erro claro ("Formato não suportado. Tente tirar a foto pela câmera ou enviar JPG/PNG") e/ou converter no FastAPI.
- **Privacidade (LGPD)**: recodificar via canvas remove metadados EXIF (inclusive GPS) do arquivo enviado — vantagem a declarar na tela de consentimento **[comportamento amplamente conhecido, não reverificado aqui]**.
- **UX do fluxo**: preview imediato com `URL.createObjectURL(blob)` (revogar depois), tela de confirmação com "Refazer"/"Usar foto", upload com progresso, e análise (~4 s) com feedback em etapas (ver seção 6). Preservar a foto em memória se o upload falhar para permitir "Tentar de novo" sem recapturar.
- Sem dependências pagas: tudo acima é API nativa; se quiser biblioteca, `browser-image-compression` (MIT) é opção comum **[não verificado]**.

### Gaps
- Comportamento exato de `capture` por plataforma (iOS Safari vs Chrome Android, se oculta ou não a galeria) não foi confirmado em fonte primária; o MDN não detalha.
- Tabelas de compatibilidade do MDN (Safari iOS para opções de `createImageBitmap` e para `OffscreenCanvas.convertToBlob`) não foram carregadas; precisa de teste em dispositivo.
- Limite de memória total de canvases no iOS (valores em MB) não confirmado; a fonte lida só traz o limite de área.
- Não encontrei fonte primária, nesta pesquisa, para o tamanho de entrada/pré-processamento do ViT-B/32 nem para qualidade "ótima" de JPEG/WebP para classificação.

---

## 5. Performance: Core Web Vitals numa SPA Vite + React

### Takeaway
Metas: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 no percentil 75 de usuários móveis. Numa SPA de guarda-roupa, o risco maior é CLS e LCP por imagens sem dimensão e fontes; reservar espaço (aspect-ratio), self-host de fonte variável e code-splitting por rota resolvem a maior parte.

### Cited Findings
- Limiar "bom": LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1; avalia-se o percentil 75 dos carregamentos, segmentado por mobile e desktop, e a página só passa se as três métricas cumprirem a meta — [web.dev Web Vitals](https://web.dev/articles/vitals)
- TTFB e FCP servem de diagnóstico para LCP lento; TBT é métrica de laboratório usada como proxy de INP — [web.dev Web Vitals](https://web.dev/articles/vitals)
- CLS acima de 0,25 é "ruim"; deslocamentos ocorridos até 500 ms após input do usuário são excluídos do cálculo — [web.dev Optimize CLS](https://web.dev/articles/optimize-cls)
- Imagens e vídeos devem ter `width`/`height` explícitos (o navegador calcula a proporção antes do download) ou espaço reservado com CSS `aspect-ratio`, combinados com `width: 100%; height: auto` — [web.dev Optimize CLS](https://web.dev/articles/optimize-cls)
- Conteúdo que demora mais de 500 ms para chegar deve ter o espaço reservado de antemão (placeholder/skeleton), e listas "carregar mais" devem trocar conteúdo dentro de contêiner de tamanho fixo ou ser disparadas pelo usuário — [web.dev Optimize CLS](https://web.dev/articles/optimize-cls)
- Fontes web: `font-display: optional` evita re-layout; alternativa é aproximar métricas do fallback com `size-adjust`, `ascent-override`, `descent-override`, `line-gap-override` e fazer preload das fontes críticas — [web.dev Optimize CLS](https://web.dev/articles/optimize-cls)
- Animações devem usar `transform` em vez de propriedades que disparam layout (`top`, `left`, `box-shadow`…); animações compostas por transform não contam para CLS — [web.dev Optimize CLS](https://web.dev/articles/optimize-cls)
- Fontsource: fontes variáveis ficam em pacotes `@fontsource-variable/<fonte>`; `import "@fontsource-variable/<fonte>"` carrega o eixo de peso; a família CSS segue o padrão `"<Fonte> Variable"`; eixos extras por arquivos como `opsz.css`, `wght-italic.css`, `full.css` (usar um único import) — [Fontsource Variable Fonts](https://fontsource.org/docs/getting-started/variable)
- Limites de percepção: 0,1 s parece instantâneo; 1 s mantém o fluxo de pensamento; 10 s é o teto de atenção — acima disso, indicador de percentual e opção de interromper — [NN/g Response Times](https://www.nngroup.com/articles/response-times-3-important-limits/)
- Skeletons: dispensáveis abaixo de 1 s; adequados a carregamentos de página inteira de ~2–10 s; acima de 10 s, barra de progresso; skeleton deve espelhar o layout final e não substitui otimização real — [NN/g Skeleton Screens](https://www.nngroup.com/articles/skeleton-screens/)

### Inferences
- **Fonte**: `npm i @fontsource-variable/dm-sans` e `import '@fontsource-variable/dm-sans'` no entry; `font-family: "DM Sans Variable", system-ui, sans-serif` (nome do pacote e da família deduzidos do padrão Fontsource — confirmar no diretório do Fontsource). Um único WOFF2 variável cobre todos os pesos; fazer preload do subset latin (`<link rel="preload" as="font" type="font/woff2" crossorigin>`) e incluir `woff2` no precache do SW. Fontsource usa `font-display: swap` por padrão **[não verificado nesta pesquisa]**; para CLS mínimo, definir um `@font-face` de fallback com `size-adjust` calibrado para DM Sans.
- **Code-splitting**: `React.lazy(() => import('./routes/Gerador'))` + `<Suspense fallback={<TelaSkeleton/>}>` por rota; manter no chunk inicial apenas shell + Home + auth; carregar sob demanda as partes pesadas (export de collage/`html-to-image`, compressão de imagem, telas de consentimento/exclusão). Pré-carregar o chunk da rota no `pointerdown`/`focus` da aba.
- **Orçamento de bundle (meta interna, não norma)**: JS inicial ≤ ~150–170 KB gzip, CSS ≤ ~30 KB, fonte ≤ ~50 KB; fiscalizar em CI com `rollup-plugin-visualizer`/`size-limit` e Lighthouse CI **[valores são julgamento de engenharia, não vieram de fonte]**.
- **Imagens**: grade do guarda-roupa com contêiner `aspect-ratio: 1/1` (ou 3/4) e `object-fit: contain` sobre fundo neutro; `<img loading="lazy" decoding="async" width height>`; a(s) imagem(ns) candidata(s) a LCP (primeira linha da grade, collage do look) **sem** `loading="lazy"` e com `fetchpriority="high"`; servir thumbs de 384–512 px na grade; placeholder com cor dominante enquanto carrega.
- **LCP em SPA**: renderizar o shell (header + tab bar + skeleton) imediatamente; não bloquear o primeiro paint esperando `getSession()` — usar o evento `INITIAL_SESSION`/sessão em cache e skeleton; paralelizar a 1ª consulta de dados com o carregamento do chunk da rota; `preconnect` para `https://<projeto>.supabase.co` e para a API.
- **INP**: mover compressão/redimensionamento para Worker quando possível; `startTransition` para filtros de chips sobre listas grandes; virtualizar a grade se passar de ~200 itens; evitar re-render global em cada tecla do prompt (estado local + debounce).
- **UI otimista**: salvar/curtir look e favoritar peça atualizam a UI na hora (ex.: `onMutate` do TanStack Query com rollback em `onError` e toast "Não foi possível salvar. Tentar de novo"), mantendo a resposta abaixo do limite de 0,1 s; operações destrutivas (excluir peça/conta) **não** otimistas — confirmar e aguardar servidor. No React 18 não há `useOptimistic` (é do React 19) **[não verificado]**.
- **Esperas longas**: geração de look e análise de foto (~4 s) caem na faixa 2–10 s → skeleton do layout final do look + texto de etapa; se passar de 10 s, mostrar progresso/etapas e botão "Cancelar".
- **Medição**: biblioteca `web-vitals` (`onLCP`, `onINP`, `onCLS`) enviando ao backend sem dados pessoais (rota, valor, tipo de conexão) **[API da lib não reverificada]**.

### Gaps
- Não busquei benchmarks publicados de orçamento de bundle para SPAs React em 2026; os números são metas internas sugeridas.
- Documentos do Fontsource sobre `font-display` e preload com Vite não foram lidos (apenas a página de fontes variáveis); nome exato do pacote DM Sans variável não foi conferido.
- Faixas "precisa melhorar" de LCP (2,5–4 s) e INP (200–500 ms) não constam da página lida.

---

## 6. Padrões de UX: apps de guarda-roupa, Material Design 3 e Apple HIG

### Takeaway
A tab bar de 5 itens está dentro do limite das duas plataformas (3–5 destinos, sempre com rótulo, sempre visível, nunca para ações). Nos apps do segmento, o maior ponto de abandono é o esforço de cadastrar o guarda-roupa; por isso remoção de fundo/auto-tag, estado vazio com caminho direto para "Adicionar peça" e feedback em etapas durante a análise por IA são os investimentos de UX de maior retorno.

### Cited Findings

**Navegação inferior**
- A documentação Android indica barra de navegação para três a cinco destinos de igual importância, em janelas compactas e com destinos consistentes entre telas — [Android Developers: Navigation bar](https://developer.android.com/develop/ui/compose/components/navigation-bar)
- Apple HIG (changelog até 08/06/2026): tab bar serve para navegar e não para ações (controles que agem na tela atual vão em toolbar); deve permanecer visível ao navegar entre seções, exceto sob um modal — [Apple HIG: Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- A Apple pede para não desabilitar nem ocultar botões da tab bar mesmo sem conteúdo — se a seção estiver vazia, explicar o motivo — e para incluir rótulos, de preferência com uma única palavra — [Apple HIG: Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- Ícones preenchidos são o padrão recomendado para consistência com a plataforma; badges ficam reservados a informação crítica; evitar cor de rótulo parecida com o fundo do conteúdo — [Apple HIG: Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- No iOS atual a tab bar flutua sobre o conteúdo com fundo Liquid Glass; no iPad a recomendação para listas customizáveis é manter cinco itens ou menos por padrão — [Apple HIG: Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)

**Estados vazios (NN/g)**
- Contêiner em branco deixa o usuário sem saber se está vazio, carregando ou quebrado; a mensagem "sem itens" não deve aparecer enquanto os dados ainda carregam (mostrar indicador de progresso) — [NN/g Empty States](https://www.nngroup.com/articles/empty-state-interface-design/)
- O estado vazio deve ensinar o que o recurso faz e como o conteúdo chega ali (ajuda em contexto é mais memorável que tutorial forçado) e oferecer caminho direto para a tarefa-chave (botão que inicia a ação), podendo incluir dados de demonstração — [NN/g Empty States](https://www.nngroup.com/articles/empty-state-interface-design/)

**Feedback de progresso (NN/g)**
- Para operações de 2 a 10 s um indicador de percentual completo pode ser exagero; o recomendado é feedback mais sutil; spinner genérico é último recurso; quando o total de trabalho é desconhecido, mostrar progresso em termos absolutos (ex.: nomear cada item/etapa processada) — [NN/g Response Times](https://www.nngroup.com/articles/response-times-3-important-limits/)

**Mensagens de erro (NN/g)**
- Diretrizes: erro próximo da origem; linguagem simples sem códigos; descrever o problema específico (evitar "Ocorreu um erro"); sugerir solução; tom neutro sem culpar (evitar "inválido"/"incorreto") e sem humor; preservar o que o usuário digitou; não exibir erro cedo demais (campo vazio durante exploração não é erro); modais bloqueantes só para erros graves — [NN/g Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)

**Apps do segmento** (atenção: as duas comparações de 2026 abaixo são publicadas por concorrentes — Wardrowbe e FITPOP — e a segunda declara não ser teste prático; tratar como indicativo)
- Whering: remoção de fundo, recurso "Dress Me" e planner com clima; gratuito com compras avulsas; críticas a sugestões pouco personalizadas e uso raso do clima — [Wardrowbe: Best Wardrobe Apps 2026](https://wardrowbe.com/blog/best-wardrobe-apps-2026/)
- Acloset: detecção de itens, looks diários, chat de stylist, try-on, feed social; gratuito até 100 itens com anúncios (sapatos, casacos e acessórios contam no limite); críticas a anúncios agressivos e looks mal coordenados — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/); [FITPOP](https://fitpop.ai/guides/digital-wardrobe-apps-compared/)
- Stylebook: tagueamento manual (configuração estimada em duas a três horas), sem sugestão por IA, compra única de US$ 4,99, só iOS — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/)
- Cladwell: looks diários, chat de stylist, prévia "See it on me", templates de cápsula; premium US$ 9,99/mês; alvo de 50–100 itens — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/)
- Indyx: looks vêm de amigos e stylists humanos (não IA), custo por uso e calendário de uso, importação de recibos por e-mail; itens ilimitados no gratuito — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/)
- Alta: looks diários a partir de guarda-roupa + clima + agenda, looks para eventos, listas de mala, try-on em avatar; gratuito — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/); [FITPOP](https://fitpop.ai/guides/digital-wardrobe-apps-compared/)
- Outros citados: Clueless (planeja 7 dias de uma vez, permite editar/regenerar qualquer dia, loop de feedback "FitCheck", setup de ~15 min) e o próprio Wardrowbe (auto-tag por visão, motor que aprende com feedback; trial de 15 itens e 3 sugestões) — [Wardrowbe](https://wardrowbe.com/blog/best-wardrobe-apps-2026/)
- Review independente (Substack, 12/09/2024): a remoção de fundo superior do Indyx permite fotografar as próprias roupas e torna menos intimidador montar o guarda-roupa; campos obrigatórios (tamanho, marca) no upload são atrito; criar look com menos passos e multi-seleção entre categorias foi elogiado; o gerador de looks do Stylebook é o recurso favorito e sua ausência no Indyx é o maior pedido; dados só no aparelho causaram perda de ~2 anos de registros ao trocar de telefone; comentarista descreve subir o guarda-roupa inteiro como "daunting" — [Rabbit Fur Coat: Indyx vs Stylebook](https://rabbitfurcoat.substack.com/p/indyx-vs-stylebook)
- Segundo o guia da FITPOP, ferramentas de remoção de fundo e colagem aparecem como diferenciais de Stylebook e Indyx — [FITPOP](https://fitpop.ai/guides/digital-wardrobe-apps-compared/)

### Inferences
- **Tab bar do StyleUp**: 5 destinos (Início, Guarda-Roupa, Gerador, Comunidade, Perfil) = limite superior aceito; rótulos sempre visíveis ("Guarda-Roupa" é o mais longo — testar a 320 px e com fonte 200%; não truncar com reticências); "Gerador" pode ter destaque visual central, mas deve continuar sendo um destino (tela), não um botão de ação, para respeitar a regra HIG. Manter a barra visível em todas as telas de primeiro nível; ocultar apenas em fluxos modais (câmera/confirmação de foto, consentimento, exclusão de conta). Estado ativo: ícone preenchido + rótulo em #4A5233 + indicador (pílula), não só mudança de cor.
- **Chips de filtro** (categoria, cor, estação): linha rolável horizontalmente com indicação de overflow, chip = `<button aria-pressed>` com ≥ 44 px de altura de toque, selecionado com check + fundo #4A5233/texto branco (8,25:1), contagem de resultados anunciada em `role="status"`, e "Limpar filtros" visível quando o resultado é vazio. Regras detalhadas de chips do Material 3 **não foram verificadas** (site exige JS).
- **Guarda-roupa vazio / onboarding**: seguir as 3 diretrizes NN/g — (1) dizer claramente "Seu guarda-roupa está vazio", (2) explicar em uma frase o que acontece ("Fotografe uma peça; a IA identifica tipo e cor em ~4 s"), (3) CTA primário "Adicionar primeira peça" + secundário "Escolher da galeria". Reduzir o "daunting": meta curta e visível ("Adicione 5 peças para gerar seu primeiro look" com progresso 2/5), nenhum campo obrigatório além da foto (IA pré-preenche; usuário corrige depois), e Gerador desbloqueado com poucas peças. A aba Gerador com guarda-roupa insuficiente deve explicar por que não gera e levar ao cadastro (não desabilitar a aba).
- **Tela de look gerado**: collage flat-lay sobre fundo neutro (o creme/branco do app) como elemento principal, tag de ocasião/estilo, descrição curta, faixa horizontal de peças (cada uma com nome + **nome da cor em texto**) e dois CTAs fixos no rodapé: "Gerar outro" (secundário) e "Salvar" (primário). É coerente com o que os reviews valorizam (colagem com fundo removido, poucos passos).
- **Feedback durante IA (~4 s)**: mensagens de etapa que mudam ("Enviando foto…" → "Identificando a peça…" → "Detectando cor…"), sobre o preview da foto; região `aria-live="polite"`; sem barra percentual falsa; se > 10 s, mostrar "Está demorando mais que o normal" + Cancelar/Tentar de novo.
- **Like/dislike/salvar**: os apps com "motor que aprende com feedback" (Wardrowbe, Clueless FitCheck) tratam o feedback como diferencial; para o StyleUp, "Salvar" = sinal positivo forte, "Gerar outro" = sinal negativo fraco, e um controle explícito opcional ("Não gostei" com motivo em chips: cor, ocasião, clima) alimenta a recomendação. Tornar visível o efeito ("Vamos sugerir menos looks assim") aumenta a percepção de controle.
- **Erros em pt-BR** no molde NN/g: "Não conseguimos analisar a foto. Verifique a conexão e tente de novo." + botão; nunca "Erro 500"/"Entrada inválida"; preservar prompt digitado e foto capturada.
- **Clima**: campo de temperatura explícito já é um diferencial frente à crítica de "uso raso do clima"; mostrar no look gerado qual temperatura foi considerada.

### Gaps
- **Material Design 3** (m3.material.io) não pôde ser lido (requer JavaScript): especificações de altura da navigation bar, indicador ativo, regras de rótulo e de filter chips ficaram sem fonte primária; só a doc Android (3–5 destinos) foi confirmada.
- **Efeito de like/dislike/salvar sobre engajamento/retenção**: não encontrei estudo ou dado quantitativo confiável; apenas descrições de recursos em material de concorrentes.
- Detalhes de UI de Whering ("Dress Me" por swipe), Pronti e de como cada app exibe o look (collage vs avatar) não foram confirmados em fonte primária ou teste independente; Pronti não apareceu em nenhuma fonte lida.
- A HIG lida não traz o número de 44×44 pt nem um máximo explícito de abas para iPhone (fala em "cinco ou menos" no contexto de customização no iPad).

---

## 7. Collage "flat-lay" no navegador e exportação como imagem

### Takeaway
Para exportar, o que decide é CORS: qualquer imagem cross-origin desenhada sem aprovação CORS "suja" o canvas e bloqueia `toBlob`. O caminho mais robusto é compor num `<canvas>` próprio a partir de blobs buscados por `fetch` (ou `<img crossOrigin="anonymous">`), exportar com `toBlob` e compartilhar via `navigator.share({ files })` quando `navigator.canShare({ files })` for verdadeiro, com download como fallback.

### Cited Findings
- Um canvas fica "tainted" assim que recebe dados de outra origem sem aprovação CORS; a partir daí `getImageData()`, `toBlob()`, `toDataURL()` e `captureStream()` lançam `SecurityError` — [MDN: CORS-enabled images](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image)
- São necessárias duas coisas: o servidor enviar `Access-Control-Allow-Origin` permitindo a origem e o elemento `<img>` pedir CORS com `crossOrigin = "anonymous"` — atribuído antes de definir `src` — [MDN: CORS-enabled images](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image)
- `html-to-image` (MIT) expõe `toPng`, `toJpeg`, `toBlob`, `toCanvas`, `toSvg`, `toPixelData`; funciona clonando o nó, copiando estilos computados, embutindo fontes e imagens como data URLs e embrulhando tudo em SVG `<foreignObject>`, que depois é desenhado em canvas — [html-to-image (GitHub)](https://github.com/bubkoo/html-to-image)
- Opções relevantes: `pixelRatio` (padrão = DPR do dispositivo), `backgroundColor`, `width`/`height`, `canvasWidth`/`canvasHeight`, `filter`, `cacheBust` (padrão `false`), `includeQueryParams` (padrão `false`: a query string fica fora da chave de cache interna), `imagePlaceholder`, `fontEmbedCSS`, `quality` — [html-to-image (GitHub)](https://github.com/bubkoo/html-to-image)
- Limitações declaradas: falha provável se houver canvas tainted no nó; árvores DOM muito grandes podem falhar por limite de tamanho de data URI; o README cita testes em Chrome, Firefox e Safari (Safari 16 à época) e desempenho melhor no Chrome — [html-to-image (GitHub)](https://github.com/bubkoo/html-to-image)
- `navigator.share(data)` aceita `url`, `text`, `title` e `files` (array de `File`); exige contexto seguro e ativação transitória (clique do usuário); rejeita com `NotAllowedError` (sem ativação/política), `AbortError` (usuário cancelou ou sem alvos), `TypeError` (dados inválidos/arquivos não suportados), `DataError`, `InvalidStateError` — [MDN: Navigator.share()](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share)
- O MDN manda testar antes com `navigator.canShare({ files })` (só `files` importa para o teste); PNG, JPEG e WebP estão entre os tipos normalmente compartilháveis; a API é "Limited availability" (fora do Baseline) — [MDN: Navigator.share()](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share)
- Limite de área de canvas no iOS Safari: 16.777.216 px — [PQINA](https://pqina.nl/blog/canvas-area-exceeds-the-maximum-limit/)

### Inferences
- **Arquitetura recomendada: um layout, dois renderizadores.** Uma função pura `layoutCollage(pieces) → [{id, x, y, w, h, z}]` em coordenadas normalizadas (0–1) por papel da peça (parte de cima, de baixo, calçado, sobreposição, acessórios). (a) Na tela: `<div>` com `aspect-ratio` fixo (ex.: 4/5) e `<img>` posicionadas em % (acessível: cada `<img>` com `alt` "Camisa branca", ou o collage como `role="img"` com `aria-label` listando peças + cores). (b) Na exportação: desenhar as mesmas caixas num `<canvas>` offscreen (ex.: 1080×1350 = 1.458.000 px, longe do limite do iOS), fundo #F2EEE3, `drawImage` com "contain".
- **Por que canvas próprio em vez de `html-to-image` como caminho principal**: resultado determinístico, sem embutir fontes/estilos, sem data URIs gigantes e sem a fragilidade histórica de `foreignObject` no Safari (imagens ausentes na 1ª renderização) **[fragilidade do Safari não verificada nesta pesquisa]**. `html-to-image` fica como opção apenas se o card exportado precisar de tipografia/CSS complexos; nesse caso carregar por `import()` dinâmico, usar `pixelRatio: 2`, `backgroundColor: '#F2EEE3'`, e manter `includeQueryParams: false` (bom para URLs assinadas cujo token muda).
- **Evitar taint com URLs assinadas do Supabase**: buscar cada imagem com `fetch(signedUrl, { mode: 'cors' })` → `blob()` → `createImageBitmap(blob)` (ou `URL.createObjectURL`), o que funciona se o Storage responder com `Access-Control-Allow-Origin` (verificar nos headers reais do projeto) **[CORS do Supabase Storage não verificado nesta pesquisa]**. Se as `<img>` da tela usarem `crossOrigin="anonymous"`, usar o atributo de forma consistente em todos os lugares — misturar requisições com e sem CORS para a mesma URL pode fazer o navegador/SW reutilizar resposta não-CORS e sujar o canvas **[não verificado]**. Cachear no SW apenas respostas CORS (status 200, não opacas).
- **Recortes**: peças com fundo removido precisam de PNG/WebP com alfa; se o backend não remover fundo, o collage fica com retângulos — usar cards arredondados com fundo branco como fallback visual.
- **Exportar e compartilhar** (esboço):
  ```ts
  const blob = await new Promise<Blob>(r => canvas.toBlob(b => r(b!), 'image/png'));
  const file = new File([blob], 'look-styleup.png', { type: 'image/png' });
  if (navigator.canShare?.({ files: [file] })) {
    try { await navigator.share({ files: [file], title: 'Meu look no StyleUp' }); }
    catch (e) { if ((e as DOMException).name !== 'AbortError') fallbackDownload(blob); }
  } else fallbackDownload(blob); // <a download> com URL.createObjectURL(blob); revogar depois
  ```
  Cuidado com a ativação transitória: se gerar o blob demorar após o toque, o `share()` pode falhar com `NotAllowedError` (especialmente no Safari) → **pré-renderizar o blob quando o look aparece** e só chamar `share()` no clique **[sensibilidade do Safari não verificada]**. Tratar `AbortError` como cancelamento silencioso.
- **Fallback de download em PWA iOS standalone**: `<a download>` pode abrir a imagem em visualização em vez de salvar **[não verificado]**; oferecer também instrução "toque e segure para salvar" exibindo a imagem num `<img>`.
- Privacidade: a imagem exportada contém só as peças (sem EXIF, sem dados pessoais); não incluir nome/e-mail no arquivo.

### Gaps
- Cabeçalhos CORS efetivos do Supabase Storage para objetos de bucket privado via URL assinada não foram verificados em documentação.
- Suporte atual (iOS Safari/Chrome Android/desktop) de Web Share com arquivos: tabela de compatibilidade do MDN não carregou; testar em dispositivo.
- Não encontrei comparação independente e recente (2026) entre `html-to-image`, `html2canvas` e alternativas quanto a bugs no Safari; versão/data do último release do `html-to-image` não constavam na página.

---

## 8. Testes e checklist de qualidade "nível produção" para SPA React em 2026

### Takeaway
A pilha gratuita padrão é Vitest + Testing Library (unidade/componente), Playwright (E2E com emulação móvel, visual e offline) e axe-core via `@axe-core/playwright`; automação de acessibilidade pega só parte dos problemas, então o checklist precisa incluir verificação manual (leitor de tela, teclado, zoom, daltonismo).

### Cited Findings
- `@axe-core/playwright`: `new AxeBuilder({ page }).analyze()` devolve `violations`; `.withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa'])` restringe às regras WCAG A/AA; `.include(seletor)` limita o escopo (esperar a UI dinâmica aparecer antes); `.exclude()` e `.disableRules([...])` suprimem itens conhecidos e devem ser usados com parcimônia — [Playwright: Accessibility testing](https://playwright.dev/docs/accessibility-testing)
- A própria doc do Playwright ressalva que muitos problemas de acessibilidade só são descobertos por teste manual e recomenda combinar automação, avaliação manual e teste com usuários — [Playwright: Accessibility testing](https://playwright.dev/docs/accessibility-testing)
- Comparação visual: `await expect(page).toHaveScreenshot()` cria a referência na 1ª execução; nome padrão inclui navegador e plataforma (ex.: `...-chromium-darwin.png`); `threshold` por pixel vai de 0 a 1 (padrão 0,2); `maxDiffPixels` limita pixels divergentes; `stylePath` injeta CSS para esconder elementos voláteis; atualização com `npx playwright test --update-snapshots` — [Playwright: Visual comparisons](https://playwright.dev/docs/test-snapshots)
- A renderização varia conforme SO, versão, configurações e hardware, logo as referências devem ser geradas e comparadas no mesmo ambiente — [Playwright: Visual comparisons](https://playwright.dev/docs/test-snapshots)
- Emulação: perfis `devices['iPhone 13']`, `devices['Pixel 5']` etc. em `projects`; opções `viewport`, `deviceScaleFactor`, `isMobile`, `locale`, `timezoneId`, `colorScheme`, `reducedMotion`, `forcedColors`, `contrast`, `offline: true`, `geolocation`, `permissions`; `locale`/`timezoneId` afetam só o navegador (para o runner usar a variável `TZ`) — [Playwright: Emulation](https://playwright.dev/docs/emulation)
- O estado vazio não deve ser confundido com carregamento ou erro: cada um precisa de representação própria — [NN/g Empty States](https://www.nngroup.com/articles/empty-state-interface-design/)
- Core Web Vitals são avaliados em campo no percentil 75 — o que justifica telemetria real além de Lighthouse de laboratório — [web.dev Web Vitals](https://web.dev/articles/vitals)

### Inferences
- **Pirâmide sugerida**
  - *Unidade/componente*: Vitest (`environment: 'jsdom'` ou `happy-dom`) + `@testing-library/react` + `@testing-library/user-event` + `@testing-library/jest-dom`; consultas por papel/nome acessível (`getByRole('button', { name: 'Salvar look' })`), o que testa de quebra os nomes acessíveis; MSW para simular FastAPI/Supabase; `vitest-axe`/`jest-axe` em componentes isolados **[nomes/estado atual desses pacotes não reverificados]**. Cobrir: `layoutCollage`, `downscale`, normalização de chave de cache, formatadores pt-BR, máquinas de estado de upload/geração.
  - *E2E (Playwright)*: projetos `Mobile Chrome` (Pixel) e `Mobile Safari` (iPhone, motor WebKit) com `viewport: { width: 390, height: 844 }`, `locale: 'pt-BR'`, `timezoneId: 'America/Sao_Paulo'`; fluxos: cadastro → consentimento → adicionar peça (upload com `setInputFiles`) → filtrar → gerar look → salvar → excluir conta; variações `offline: true` (fallback), `reducedMotion: 'reduce'`, API lenta/erro (via `page.route`).
  - *A11y automatizada*: AxeBuilder em cada tela e em cada estado (vazio, carregando, erro, diálogo aberto) com tags `wcag2a, wcag2aa, wcag21a, wcag21aa` + `wcag22aa` (tag do axe-core para regras 2.2 como tamanho de alvo) **[existência da tag `wcag22aa` não confirmada na doc lida]**; falhar o CI com `violations.length > 0`.
  - *Visual*: `toHaveScreenshot` por tela no frame 390×844, com `animations: 'disabled'` e `mask` em áreas dinâmicas **[opções não constavam na página lida]**; gerar baselines sempre no mesmo contêiner/CI (imagem Docker oficial do Playwright).
  - *Lighthouse*: Lighthouse CI com orçamento (Performance, Accessibility, Best Practices) em modo mobile; a categoria "PWA" foi removida do Lighthouse em versões recentes, então instalabilidade deve ser checada no painel Application do DevTools e por teste E2E do manifest/SW **[não verificado nesta pesquisa]**.
- **Checklist de qualidade de produção (por tela assíncrona: Home, Guarda-Roupa, Gerador, Look, Perfil, Comunidade)**
  1. Quatro estados implementados e testados: carregando (skeleton fiel ao layout), vazio (mensagem + CTA), erro (mensagem específica + "Tentar de novo"), sucesso; mais estado offline.
  2. `ErrorBoundary` por rota (ex.: `react-error-boundary`, MIT) com tela de recuperação e relatório de erro sem PII; boundary global para falha de chunk (`import()` rejeitado após deploy → oferecer recarregar/atualizar SW).
  3. Formulários: validação no submit/blur (não a cada tecla), erros em texto junto ao campo com `aria-describedby` + `aria-invalid`, foco no primeiro erro, entrada preservada, `autocomplete` correto, `inputmode`/`type` adequados (e-mail, numérico para temperatura), botão de submit com estado "Enviando…" e proteção contra duplo envio.
  4. i18n pt-BR: `<html lang="pt-BR">`; `Intl.DateTimeFormat('pt-BR')`, `Intl.NumberFormat('pt-BR')` (vírgula decimal), `Intl.RelativeTimeFormat`, `Intl.PluralRules` para "1 peça / 2 peças"; temperatura como `22 °C`; strings centralizadas (mesmo sem lib de i18n) para revisão de tom; nomes de cores em português como texto.
  5. Acessibilidade manual: navegação completa por teclado/Switch Control; VoiceOver (iOS) e TalkBack (Android) nos fluxos principais; zoom de texto 200% e largura 320 px; simulação de daltonismo (DevTools → Rendering) conferindo que nenhuma informação depende de cor; `prefers-reduced-motion`.
  6. PWA: manifest válido, ícones (incl. maskable e apple-touch-icon), instalação testada em Android (Chrome) e iPhone (Safari), safe areas em aparelho com notch/home indicator, atualização via prompt, logout limpa caches e stores por usuário, comportamento offline.
  7. Performance: CWV no p75 dentro das metas em rede 4G simulada; orçamento de bundle no CI; imagens com dimensões reservadas.
  8. Segurança/privacidade (LGPD): nenhum token/URL assinada/e-mail em logs ou telemetria; telemetria com eventos agregados (nome do evento, rota, duração, código de erro) e ID pseudônimo ou nenhum; consentimento registrado antes de upload de fotos; fluxo de exclusão de conta testado ponta a ponta (apaga objetos do Storage e caches locais); CSP e `Referrer-Policy: no-referrer` para não vazar URLs assinadas **[boas práticas gerais, não vieram de fonte lida]**.
  9. Robustez: timeouts e `AbortController` em todas as chamadas, retry com backoff só para GET idempotente, cancelamento ao sair da tela, tratamento de sessão expirada (401 → renovar/reencaminhar ao login preservando a rota de destino).
  10. Qualidade de código: TypeScript `strict`, ESLint com `eslint-plugin-jsx-a11y` e `react-hooks`, checagem de tipos e testes no CI, revisão de dependências (sem pacotes pagos).

### Gaps
- Documentação do Vitest e da Testing Library não foi lida nesta pesquisa (limite de chamadas); as recomendações dessa camada são de conhecimento prévio.
- Não confirmei na doc do axe-core a lista de tags (`wcag22aa`) nem quais regras 2.2 (ex.: `target-size`) vêm habilitadas por padrão.
- Estado atual do Lighthouse (remoção da categoria PWA; versão vigente em 11/2026) não verificado.
- Não encontrei um checklist "AAA/produção" canônico e independente para SPAs; a lista acima é síntese de boas práticas apoiada nas fontes de WCAG, NN/g, web.dev e Playwright citadas nas outras seções.
