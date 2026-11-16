# Recomendação de looks por regras (menswear): harmonia de cor, compatibilidade, diversidade do top-K e aprendizado por like/dislike

> Convenções destas notas: **[EMP]** = achado empírico revisado por pares; **[PRE]** = preprint/artigo sem avaliação robusta; **[OPI]** = opinião de praticante (guia de estilo). "Inferences" são sugestões de engenharia minhas, não afirmações das fontes. Cálculos marcados "cálculo próprio" foram feitos por mim com as fórmulas citadas (script Python, conversão sRGB→CIELAB D65) e não constam das fontes.

## 1. Quais modelos de harmonia de cor têm suporte empírico e o que dizem sobre matiz, luminosidade e croma? (Ou & Luo, Cohen-Or/Matsuda, O'Donovan, Schloss & Palmer, Itten/Munsell)

### Takeaway
Os estudos empíricos convergem em três pontos que o score atual do StyleUp ignora: (a) harmonia cai de forma aproximadamente monotônica com a diferença de matiz/croma (não há "bônus de complementar" confiável), (b) diferença de luminosidade entre as duas cores aumenta a harmonia até saturar por volta de ΔL* ≈ 15–20, e (c) croma baixo/cores frias ajudam; os templates de matiz (Itten/Matsuda) são convenção de design com pouca evidência de preferência real. Nenhum dos estudos recuperados foi validado em roupas — todos usam patches ou paletas — e o modelo de Ou & Luo aplicado "cru" a pares clássicos de menswear (navy+cáqui, marrom+navy) dá notas baixas, então a estrutura serve, mas os coeficientes precisam de recalibração.

### Cited Findings

**Ou & Luo — modelo de harmonia para duas cores (CIELAB)**
- [EMP] As equações abaixo aparecem em Ou, Luo & Cui, "A Colour Design Tool Based on Empirical Studies" (DRS 2008, versão depositada), seção do Experimento 3, ajustadas sobre 1.431 pares de cores avaliados por 17 participantes; a lista de referências do artigo inclui Ou & Luo (2006), "A colour harmony model for two-colour combinations" — [Ou, Luo & Cui 2009](https://core.ac.uk/download/100025.pdf)

```
CH   = H_C + H_L + H_H

H_C  = 0.04 + 0.53·tanh(0.8 − 0.045·ΔC)
ΔC   = sqrt( (ΔH*ab)² + (ΔC*ab / 1.46)² )

H_L    = H_Lsum + H_ΔL
H_Lsum = 0.28 + 0.54·tanh(−3.88 + 0.029·L_sum),   L_sum = L*1 + L*2
H_ΔL   = 0.14 + 0.15·tanh(−2 + 0.2·ΔL),           ΔL = |L*1 − L*2|

H_H  = H_SY1 + H_SY2
H_SY = E_C·(H_S + E_Y)
E_C  = 0.5 + 0.5·tanh(−2 + 0.5·C*ab)
H_S  = −0.08 − 0.14·sin(h_ab + 50°) − 0.07·sin(2·h_ab + 90°)
E_Y  = [(0.22·L* − 12.8)/10]·exp{ (90° − h_ab)/10 − exp[(90° − h_ab)/10] }
```
(L*, C*ab, h_ab = luminosidade, croma e ângulo de matiz CIELAB; ΔH*ab = diferença métrica de matiz CIELAB.)
- [EMP] Princípios verbais que acompanham o modelo: duas cores de mesmo matiz e croma que só diferem em luminosidade tendem a parecer harmoniosas; quanto mais clara cada cor, maior a chance de harmonia; diferenças pequenas de luminosidade reduzem a harmonia; azul é o matiz que mais favorece harmonia e vermelho o que menos favorece; amarelos claros harmonizam mais que amarelos escuros (cáqui) — [Ou, Luo & Cui 2009](https://core.ac.uk/download/100025.pdf)
- [EMP] Limitação declarada pelos autores: os dados vêm de patches chapados sobre fundo cinza médio, julgados por estudantes chineses no Reino Unido; pode não generalizar para outras formas, texturas, idades ou culturas — [Ou, Luo & Cui 2009](https://core.ac.uk/download/100025.pdf)

**Cohen-Or et al. 2006 — "Color Harmonization" (templates de Matsuda)**
- Os oito templates harmônicos sobre a roda de matiz HSV (tipos i, V, L, I, T, Y, X, N) vêm dos esquemas de Matsuda, que descendem da teoria de Itten; Tokumaru et al. (2002) já os usavam para avaliar harmonia — [Cohen-Or et al. 2006](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/07/harmonization.pdf)
- Tamanhos de setor publicados no apêndice: i = 18° (5% da roda); V = 93,6° (26%); L = 79,2° (22%) + 18°, centros a 90°; I = dois setores de 18° a 180°; T = 180° (50%); Y = 93,6° + 18° a 180°; X = dois de 93,6° a 180°; N = escala de cinza (não tratado). O template pode girar por qualquer ângulo α — [Cohen-Or et al. 2006](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/07/harmonization.pdf)
- Função de distância à harmonia: F(X,(m,α)) = Σ_p ‖H(p) − E_Tm(α)(p)‖ · S(p), isto é, distância em arco do matiz até a borda do setor mais próximo, ponderada pela saturação; matiz dentro do setor tem distância zero. A justificativa da ponderação é que diferenças entre cores pouco saturadas são menos perceptíveis — [Cohen-Or et al. 2006](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/07/harmonization.pdf)
- O método só mexe no canal de matiz (o artigo afirma que harmonia "is mainly affected by the hue channel"), não altera regiões escuras/cinzas e deixa transformações de saturação e luminosidade como trabalho futuro — [Cohen-Or et al. 2006](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/07/harmonization.pdf)

**O'Donovan, Agarwala & Hertzmann 2011 — "Color Compatibility From Large Datasets"**
- [EMP] Dados: Kuler (104.426 temas de 5 cores; 327.381 notas de 22.376 usuários), COLOURLovers (383.938 temas) e Mechanical Turk (10.743 temas, ~40 avaliadores cada, 1.301 participantes) — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Os autores encontraram pouca evidência de que pessoas gravitem naturalmente para templates de matiz ou de que aderir a um template renda nota maior; os templates extras de Matsuda quase não aparecem, e os frequentes são os que a própria interface do Kuler oferece — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] A preferência não é invariante à rotação da roda de cores: verde aparece mais com azul ou amarelo do que com seu complementar (roxo); matizes quentes e ciano têm alta "adjacência", verde e roxo são relativamente impopulares — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Número de matizes: temas monocromáticos ou com mais de 2–3 matizes tendem a receber notas piores (no MTurk o monocromático não é penalizado, mas mais cores piora) — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Luminosidade é fator de primeira ordem: luminosidade média é a feature mais importante no MTurk; temas escuros são mal avaliados salvo se houver ao menos uma cor clara; gradientes claro→escuro são preferidos — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Modelo preditivo: regressão LASSO sobre 334 features (RGB, CIELAB, HSV, CHSV); MAE cai de 0,267 (baseline fixo) para 0,179 no MTurk; acurácia bom/ruim de 77,4% (MTurk), 64,2% (Kuler), 60,1% (COLOURLovers) — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Diferenças individuais: concordância entre usuários de 52% (perto do acaso) no geral e 81% dentro de 10 clusters de usuários; um modelo de mistura personalizado reduz o MAE de 1,30 para 1,00 com 20 notas do usuário — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)

**Schloss & Palmer 2011 — "Aesthetic response to color combinations: preference, harmony, and similarity"**
- [EMP] 48 participantes; 32 cores cromáticas (8 matizes × 4 "cortes": saturado, claro, apagado/muted, escuro); 992 pares figura-fundo — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [EMP] Preferência pelo par e harmonia atingem o máximo quando os dois matizes coincidem e caem conforme a diferença de matiz cresce; a correlação entre similaridade percebida e harmonia é r = +0,83 — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [EMP] Complementares não mostram aumento confiável de preferência nem de harmonia (a harmonia até cai para complementares de pintura); a "harmonia de contraste" de Chevreul não se sustenta para pares, só a "harmonia de análogas"; a teoria de Itten é descrita, mas não testada — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [EMP] Contraste de luminosidade pesa mais na preferência do que na harmonia (harmonia × diferença de luminosidade: r = +0,10); a cor da figura é mais apreciada sobre fundo de luminosidade contrastante — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [EMP] O melhor modelo de harmonia explica 67,3% da variância e favorece matizes semelhantes, cores mais frias, menor saturação e "frieza" semelhante; o modelo de preferência (dimensões Munsell) explica 53,5% — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [EMP] Harmonia ≠ preferência: correlacionam r = +0,79 (~62% de variância comum); a concordância entre observadores é maior para harmonia (r médio +0,51) do que para preferência (+0,36); a preferência individual por harmonia varia de +0,75 a −0,03 — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)

### Inferences
- **Avaliação do score atual do StyleUp à luz da evidência.** (i) A faixa "≥150° = 0,70" maior que "60–150°" replica o template complementar (tipo I de Matsuda: dois setores de 18° a 180°), mas Schloss & Palmer e O'Donovan não encontram vantagem empírica para complementares; a queda com Δmatiz é monotônica. (ii) O score ignora ΔL e croma, que nas três fontes empíricas pesam tanto quanto ou mais que o matiz. (iii) "neutro+cor = 1,0" é coerente com a ponderação por saturação de Cohen-Or (diferença de matiz em cor pouco saturada quase não conta) e com o termo E_C de Ou & Luo (efeito de matiz praticamente desligado abaixo de C* ≈ 4 e ligado acima de C* ≈ 8 — cálculo próprio: E_C = 0,02 em C*=0; 0,50 em C*=4; 0,98 em C*=8).
- **Leitura numérica do modelo Ou & Luo (cálculo próprio a partir das equações):**
  - H_ΔL: −0,005 (ΔL*=0); 0,03 (5); 0,14 (10); 0,25 (15); 0,285 (20); satura em 0,29 a partir de ~25. → limiar prático: **ΔL* < 5 = sem contraste; ≥ 15–20 = contraste pleno**.
  - H_C: +0,39 (ΔC=0); +0,22 (10); +0,04 (≈18); −0,23 (30); −0,44 (50); piso ≈ −0,49 (≥70). Como ΔH*ab = 2·√(C1·C2)·sin(Δh/2), a penalidade de matiz já é automaticamente escalada pelo croma das duas cores.
  - H_Lsum: −0,26 (L_sum ≤ 40) … +0,08 (120) … +0,28 (134) … +0,63 (160) … +0,80 (200): é o termo de maior amplitude e favorece pares claros.
  - H_S por matiz CIELAB: mínimo ≈ −0,26 em h≈0–30° (vermelhos), ≈ −0,10 em 90° (amarelo), máximo ≈ +0,09 em h≈240–270° (azuis).
  - Faixas dos termos: H_C ∈ [−0,49; +0,39], H_Lsum ∈ [−0,26; +0,80], H_ΔL ∈ [0; +0,29]; CH total fica aproximadamente entre −1,5 e +1,9 → para usar como score 0–1, normalizar por min-max sobre os pares possíveis do guarda-roupa.
- **O modelo cru não reproduz convenções de menswear (cálculo próprio, hex ilustrativos):** bege+branco 1,32; cinza+branco 1,24; charcoal+azul-claro 0,67; denim+branco 0,61; preto+branco 0,59; navy+branco 0,54; navy+cinza 0,27; preto+navy 0,16; preto+marrom 0,02; **navy+cáqui −0,18; marrom+navy −0,44; oliva+navy −0,43**; denim+marrom −0,68; burgundy+navy −0,79; vermelho+verde −0,89. Os clássicos navy+cáqui e marrom+navy saem negativos porque H_Lsum pune pares escuros e H_C pune diferença de croma/matiz mesmo entre cores de croma moderado. Conclusão de engenharia: aproveitar a **forma** (tanh em ΔL, distância cromática ponderada por croma, gate de neutro por C*), mas (1) remover ou reduzir muito H_Lsum (roupa masculina é predominantemente escura), (2) manter override de neutros/quase-neutros, (3) descartar E_Y (pune cáqui/oliva, que são básicos de menswear).
- **Proposta de score de cor por par (0–1), derivada das fontes acima:**
  1. Converter a cor dominante de cada peça para CIELAB (L*, C*, h).
  2. `neutro_acromático`: C* < ~8–10 (preto, branco, cinza). `quase-neutro`: lista nominal {navy, bege/cáqui, marrom, oliva, denim} — nos hex testados navy, bege, cáqui e marrom têm C* ≈ 15–19 (um corte C* ≤ 20 os captura), mas oliva e denim têm C* ≈ 34–36 e precisam de flag por categoria/material.
  3. Termo cromático: se algum dos dois é neutro/quase-neutro → 1,0 (0,9 se ambos neutros e ΔL* < 10, para refletir o "washed out"); senão `s_hc = minmax(0.04 + 0.53·tanh(0.8 − 0.045·ΔC))`.
  4. Termo de contraste de valor: `s_ΔL = clamp((ΔL* − 5)/15, 0, 1)`, aplicado sobretudo ao par top–bottom.
  5. Termo de saturação: penalizar dois itens de croma alto (ex.: ambos C* > 50) com matizes diferentes — coerente com "menor saturação → mais harmonia" (Schloss & Palmer) e com "1–2 acentos pequenos" dos guias.
  6. Combinar, por exemplo, `par = 0.5·s_hc + 0.3·s_ΔL + 0.2·s_sat`, e agregar os pares ponderando por área visível (top–bottom > bottom–shoes > top–shoes). Os pesos 0,5/0,3/0,2 são ponto de partida meu, a calibrar com os likes.
- Como harmonia tem mais consenso entre pessoas (r=0,51) do que preferência (r=0,36), faz sentido manter o score de cor como regra global e deixar a personalização para o critério "estilo aprendido".

### Gaps
- Não consegui abrir o texto primário de Ou & Luo (2006), Color Research & Application 31(3), DOI 10.1002/col.20208 (paywall; a página de resumo voltou vazia). As equações acima vêm do artigo de 2009 dos mesmos autores, que cita o de 2006; conferir os coeficientes no original antes de citar em relatório acadêmico.
- Não recuperei nenhum estudo empírico de harmonia de cor feito **com roupas/looks** (tecido, textura, corpo); todos os achados acima são de patches ou paletas. Também não recuperei fontes primárias de Itten, Munsell ou Moon & Spencer (1944); as menções a Itten/Chevreul/Munsell vêm de segunda mão (Cohen-Or; Schloss & Palmer).
- A escala exata de saída de CH (categorias do experimento) não foi verificada.

## 2. Regras práticas de cor em menswear (número de cores, neutros, tons terrosos, monocromático/tonal, contraste top/bottom, sapato/cinto, combinações "proibidas")

### Takeaway
Os guias concordam em: base de neutros na maior parte da área, no máximo 1–2 cores de destaque em área pequena (estrutura "âncora / secundária / acento", ~3 cores), contraste suficiente entre peças (por tom, textura ou padrão) e couros coordenados; "preto com navy" e "preto com marrom" **não** são proibições — são pares que exigem intenção e contraste claro. Tudo aqui é opinião de praticante, com apoio empírico parcial apenas para "2–3 matizes" (O'Donovan).

### Cited Findings
- [OPI] Estrutura de três cores: looks bem-sucedidos costumam girar em torno de três cores principais (âncora, secundária, acento terciário); looks de duas cores são opção válida; quatro ou cinco funcionam se as cores extras ocuparem área mínima. Nos exemplos, neutros **contam** como cores da paleta — [Real Men Real Style, "3 color outfits"](https://www.realmenrealstyle.com/3-color-outfits/)
- [OPI] 60/30/10: uma cor dominante (maior área visível — terno, casaco, ou conjunto jaqueta+calça), uma de apoio (camisa, malha ou calça contrastante) e um acento (gravata, lenço, meias, sapato, pulseira); os números devem ser lidos como ênfase relativa, não medida; não há máximo fixo de cores nem regra fixa para contar neutros; looks de duas cores e tonais (profundidades diferentes de uma cor) são exceções aceitas — [TheVou, "6 3 1 Colour Rule for Men"](https://thevou.com/blog/golden-rule-of-colour-men/)
- [OPI] Lista de neutros como base: preto, branco, cinza, navy, marrom, tan e alguns olivas ("canvas" do estilo) — [RMRS, "3 color outfits"](https://www.realmenrealstyle.com/3-color-outfits/); outra lista do mesmo site inclui preto, branco, cinza, navy/azul-claro/sky blue, marrom/cáqui e verde-oliva, diz que neutros devem ser a maior parte do guarda-roupa e que cores vivas entram em "small touches of 1-2 brighter colors" — [RMRS, "match colors style rules"](https://www.realmenrealstyle.com/match-colors-style-rules/)
- [OPI] Taxonomia de neutros: quentes (tan, taupe, bege, marfim, cáqui, qualquer marrom) e frios (preto, cinza, branco); navy, azul e verde-oliva "strictly speaking, they're not neutrals", mas combinam bem com neutros — [Gentleman's Gazette, "How to Wear & Pair Neutrals"](https://www.gentlemansgazette.com/how-to-wear-neutrals/)
- [OPI] Preto, branco e cinza combinam com qualquer cor (ajustando o brilho do cinza à paleta); marrom, tan, creme, bege e cáqui são tratados como neutros e navy "can work well as a 'neutral' too" — [Ape to Gentleman, "How to Colour Match Clothing"](https://www.apetogentleman.com/colour-match/)
- [OPI] Combinar neutros entre si: evitar tons parecidos demais (o resultado fica "washed out"); criar contraste por textura, padrão e escala; sem contraste o look se funde; monocromático (tudo da mesma cor) pode ficar chapado — [Gentleman's Gazette, neutrals](https://www.gentlemansgazette.com/how-to-wear-neutrals/)
- [OPI] Esquemas da roda de cores: monocromático (um matiz variando brilho e saturação), análogo (2–3 matizes vizinhos, idealmente com saturação e brilho iguais), complementar (opostos; "likely to be too much" sem ajuste de saturação/brilho), triádico (difícil; dominar os outros antes). Regra-resumo: escolher duas cores (ou uma) e manter constante ao menos um entre matiz, saturação e brilho; neutros entram livremente — [Ape to Gentleman](https://www.apetogentleman.com/colour-match/)
- [OPI] Complementares vermelho+verde em tons ou proporções erradas fazem o usuário parecer "a Christmas decoration" — [RMRS, match colors](https://www.realmenrealstyle.com/match-colors-style-rules/)
- [OPI] Sapatos: marrom complementa a maioria dos neutros melhor que preto; preto fica para casos formais — [RMRS, match colors](https://www.realmenrealstyle.com/match-colors-style-rules/). Cinto e sapato costumam ser neutros (marrom ou preto) e amarram o look — [RMRS, 3 color outfits](https://www.realmenrealstyle.com/3-color-outfits/)
- [OPI] Couros e metais: a regra tradicional é casar couros e metais, mas pode ser flexionada com bom gosto (ex.: cinto marrom mais escuro com sapato marrom um pouco mais claro) — [Gentleman's Gazette, "11 Bad Men's Style Rules to Ignore"](https://www.gentlemansgazette.com/11-bad-mens-style-rules-to-ignore/)
- [OPI] Preto + marrom: podem ser usados juntos se as peças harmonizarem em intensidade e formalidade; o que incomoda são pretos "quase iguais mas não exatamente" — [Gentleman's Gazette, 11 bad rules](https://www.gentlemansgazette.com/11-bad-mens-style-rules-to-ignore/). Dan Rookwood (Mr Porter) raramente mistura preto com marrom ("looks off to my eye"), mas afirma que não é errado, é preferência — [Mr Porter 2017](https://www.mrporter.com/en-es/journal/fashion/you-asked-can-you-wear-black-and-navy-together-762234)
- [OPI] Preto + navy: a proibição é tratada como regra antiga que não resiste a escrutínio; condição: parecer deliberado. Evitar calça preta com blazer navy (parece erro); funcionam jeans índigo + jaqueta de couro preta ou jeans preto + bomber navy — [Mr Porter 2017](https://www.mrporter.com/en-es/journal/fashion/you-asked-can-you-wear-black-and-navy-together-762234)
- [OPI] Tom de pele pesa cerca de 10% da decisão de cor e só depois das regras de neutros e acentos — [RMRS, match colors](https://www.realmenrealstyle.com/match-colors-style-rules/)
- [EMP, paletas] Paletas com 2–3 matizes recebem as melhores notas; mais matizes pioram — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [PRE] Um recomendador híbrido publicado em 2026 implementa a regra como penalidade `P_color = 0.1 · max(0, n_non-neutral − 2)` — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)

### Inferences
- Regras de outfit (nível do look inteiro, não do par) que o StyleUp pode codificar:
  - `n_cores_não_neutras` (famílias de matiz distintas, agrupando por ~30°): 0–2 → sem penalidade; cada cor adicional → −0,10 (valor do Loom) ou −0,15.
  - Bônus de "base neutra": ≥ 60% da área (top+bottom, ou outer+bottom) em neutros/quase-neutros.
  - Pesos de área aproximando 60/30/10: peça dominante (outer se houver, senão top ou bottom) ≈ 0,6 do peso; segunda peça ≈ 0,3; sapatos+acessórios ≈ 0,1. A cor de acento saturada deve estar na fatia de 10–30%.
  - Preto+navy e preto+marrom: não penalizar pelo par em si; penalizar só **baixo contraste de valor** (ΔL* < ~10) entre peças adjacentes de área grande. Nos hex testados, preto×navy tem ΔL* ≈ 12 e preto×charcoal ≈ 23 (cálculo próprio), ou seja, navy escuro com preto fica no limite — coerente com a ressalva "calça preta + blazer navy parece erro".
  - Tonal/monocromático: aceitar quando Δmatiz ≤ ~15–20° e ΔL* ≥ 10–15 entre top e bottom (ou textura/material diferentes); penalizar "mesma cor, mesmo tom" exceto conjunto/terno.
  - Sapato–cinto: mesma família de couro (marrom com marrom, preto com preto) = 1,0; marrons de tons diferentes = 0,8–0,9; preto+marrom = 0,5.
- Tons terrosos (marrom, cáqui, oliva, bege, tan) aparecem nas listas de neutros/quase-neutros de três guias; tratar combinações terroso+terroso como neutro+neutro (com exigência de ΔL*), não pelo ângulo de matiz.

### Gaps
- Não encontrei, nas fontes abertas, uma regra numérica de praticante para contraste de valor top/bottom (ex.: "top mais claro que bottom"); só a orientação qualitativa de evitar tons muito próximos. O limiar ΔL* ≈ 10–20 vem do modelo de Ou & Luo, não de guias de estilo.
- Permanent Style e Put This On não foram consultados para regras de cor (apenas Put This On para padrões); GQ/Esquire não foram consultados.
- Nenhuma fonte recuperada trata de preferências regionais brasileiras ou de clima quente em escolha de cor (ex.: cores claras no calor).

## 3. Jeans azul (denim) deve ser tratado como neutro?

### Takeaway
Sim, com base em opinião de praticante: o Gentleman's Gazette diz explicitamente que denim pode ser chamado de neutro (embora azul/navy não sejam neutros "estritos"), e outros guias colocam navy/azuis na base neutra. Não há evidência empírica; recomenda-se tratar denim azul como quase-neutro via flag de material, não via cor.

### Cited Findings
- [OPI] Navy, azul e oliva não são neutros no sentido estrito, mas combinam bem com neutros; denim é a exceção que, segundo o autor, "can definitely be called a neutral color" — [Gentleman's Gazette, neutrals](https://www.gentlemansgazette.com/how-to-wear-neutrals/)
- [OPI] A lista de neutros-base do RMRS inclui "navy/light/sky blue" — [RMRS, match colors](https://www.realmenrealstyle.com/match-colors-style-rules/); Ape to Gentleman aceita navy como neutro — [Ape to Gentleman](https://www.apetogentleman.com/colour-match/)
- [OPI] Em smart casual, o bottom padrão é jeans índigo escuro sem rasgos nem lavagem marcada — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Jeans índigo com jaqueta de couro preta é citado como combinação preto+azul que funciona — [Mr Porter 2017](https://www.mrporter.com/en-es/journal/fashion/you-asked-can-you-wear-black-and-navy-together-762234)
- [PRE] Em uma tabela de regras publicada (escala 0–10), T-shirt+jeans vale 8 e botas+jeans 9; o texto dá 7 para camisa+jeans contra 9 para camisa+calça clássica — [Kazarian et al. 2025](https://heraldts.khmnu.edu.ua/index.php/heraldts/article/download/1962/1879/6445)

### Inferences
- Implementar `is_neutral = cor ∈ neutros OR (material == denim AND matiz azul/índigo/preto/cinza)`. Um azul-denim médio tem C* ≈ 34 e h ≈ 280° (cálculo próprio com #3B5B92), então **não** seria classificado como neutro por limiar de croma — precisa da flag de material/categoria.
- Sugestão de score: denim azul + qualquer cor = 0,95 (levemente abaixo de neutro acromático = 1,0), mantendo a checagem de ΔL* (denim escuro + top navy escuro = baixo contraste). Denim colorido (vermelho, verde) não herda o status de neutro.
- O status de neutro é de **cor**; a formalidade do denim continua restrita (ver seção 6: jeans "nunca" em dress casual, raramente em business casual).

### Gaps
- Não encontrei fonte aberta e confiável sobre "denim com denim" (top e bottom jeans) nem sobre diferença de lavagem necessária; tratar como regra a validar com usuários.
- Nenhuma evidência empírica (estudo com avaliadores) sobre denim como neutro foi localizada.

## 4. O que a pesquisa em fashion compatibility learning (Polyvore etc.) e os recomendadores baseados em regras ensinam para regras escritas à mão?

### Takeaway
A literatura neural mostra que (a) compatibilidade depende do **par de tipos** (top–bottom ≠ bottom–sapato), (b) é multi-nível — cor e textura em baixo nível, estilo em alto nível — e (c) melhora quando o look é avaliado como um todo, não só como média de pares. Os poucos recomendadores por regras publicados usam soma de bônus/penalidades com constantes escolhidas à mão e têm avaliação fraca; servem como referência de design, não de evidência.

### Cited Findings
- [EMP] Han et al. 2017 tratam o outfit como sequência (top → bottom → acessórios), usam Bi-LSTM para prever o próximo item e um embedding visual-semântico (atributos e categorias) como regularização; tarefas: completar um look, gerar look a partir de imagem/texto e prever compatibilidade, em dataset coletado do Polyvore — [Han et al. 2017, arXiv:1707.05691](https://arxiv.org/abs/1707.05691)
- [EMP] Vasileva et al. 2018 aprendem um embedding que respeita o tipo do item e separa **similaridade** (duas peças intercambiáveis) de **compatibilidade** (peças de tipos diferentes que formam um look); usam 68.306 outfits do Polyvore e relatam ganho de 3–5% sobre o estado da arte em compatibilidade e fill-in-the-blank — [Vasileva et al. 2018, arXiv:1803.09196](https://arxiv.org/abs/1803.09196)
- [EMP] Wang et al. 2019 (MCN) calculam a nota do outfit a partir de similaridades par-a-par específicas por tipo e comparam features de várias camadas da CNN, de aspectos de baixo nível (cor, textura) a alto nível (estilo); gradientes são usados para diagnosticar qual item/aspecto torna o look incompatível; dataset Polyvore-T — [Wang et al. 2019, arXiv:1907.11496](https://arxiv.org/abs/1907.11496)
- [EMP] Plummer et al. 2019 (SANE) explicam por que dois itens "combinam" apontando região saliente + atributo, avaliando no Polyvore Outfits — [Plummer et al. 2019, arXiv:1905.10797](https://arxiv.org/abs/1905.10797)
- [EMP] OutfitTransformer (Sarkar et al. 2022) aprende uma representação do outfit inteiro com self-attention e um token de outfit, modelando a compatibilidade entre todos os itens de uma vez, e relata superar o estado da arte em compatibilidade, FITB e recuperação de item complementar — [Sarkar et al. 2022, arXiv:2204.04812](https://arxiv.org/abs/2204.04812)
- [PRE] Loom (Berlia, maio/2026): score composto `S = S_similarity + B_style + B_color_harmony − P_color_clash − P_formality_gap − P_occasion_conflict − P_statement_overload`; pesos por slot na similaridade: bottoms 0,35, shoes 0,25, accessories 0,15, layer 0,10, top 0,10, mais termo cruzado bottom–shoe de 0,05; `P_color = 0.1·max(0, n_non-neutral − 2)`; `P_form = 0.2·max(0, Δℓ − 1)` com níveis de formalidade ℓ ∈ {0,1,2}; penalidade de 0,15 quando os conjuntos de ocasião dos itens não se sobrepõem; penalidade de "statement overload" 0,1·(n_statement − 1) — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)
- [PRE] Avaliação do Loom: catálogo de 620 itens, 150 outfits por configuração; sistema completo com score 0,179 e 9,3% de violações "hard" contra 0,054 e 16,0% do baseline aleatório; remover a penalidade de compatibilidade de material **melhorou** o score (0,233; 4,7% de violações), o que os autores atribuem a penalidade conservadora demais; a métrica principal é a própria função de score (risco de circularidade) e falta estudo com humanos — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)
- [PRE] Kazarian et al. 2025 (Lviv Polytechnic): filtra o guarda-roupa por clima e estilo, agrupa em top/bottom/calçado/(outerwear), enumera combinações, pontua e devolve as 5 melhores; compatibilidade de tipo `S = (C_vt + C_vs + C_ts)/N` e de cor `S_c = (C_cv + C_ct + C_cs)/N` com coeficientes tabelados 0–10 (ex.: preto–branco 9, navy–cinza 8, preto–azul 7, branco–vermelho 7, azul–bege 6, verde–marrom 6); sem pesos entre critérios, sem limiares numéricos de clima e sem métricas de avaliação — [Kazarian et al. 2025](https://heraldts.khmnu.edu.ua/index.php/heraldts/article/download/1962/1879/6445)

### Inferences
- Para o StyleUp: (1) pontuar pares **por tipo de par** com pesos distintos (top–bottom, bottom–shoes, top–shoes, outer–top), em vez de média simples de todos os pares; (2) acrescentar termos de nível de outfit (nº de cores não neutras, nº de peças "statement"/estampadas, amplitude de formalidade) além da média de pares; (3) guardar o detalhamento por termo para explicar o look ("combina porque…"), no espírito do diagnóstico do MCN/SANE.
- A ablação do Loom é um alerta: penalidade manual mal calibrada pode piorar o resultado; cada regra nova do StyleUp deveria ser testada ligando/desligando contra os likes reais.
- A arquitetura atual do StyleUp (soma ponderada de 5 critérios + top-3) é do mesmo tipo dos sistemas por regras publicados; o diferencial possível é ter avaliação com usuários (HR@3/P@3), que nenhum dos dois artigos por regras apresenta.

### Gaps
- Não verifiquei nesta sessão Cucurull et al. 2019 ("Context-Aware Visual Compatibility Prediction", grafo de itens) nem números de FITB/AUC dos artigos — os resumos não trazem valores.
- Não localizei estudo que quantifique a **importância relativa** de cor vs. tipo vs. estilo vs. padrão em compatibilidade (ex.: ablação por atributo); a afirmação "cor e textura em baixo nível, estilo em alto nível" é qualitativa (MCN).
- Os datasets Polyvore são majoritariamente de moda feminina; a transferência para menswear não é discutida nos resumos consultados.

## 5. Regras de mistura de padrões (liso / listrado / xadrez / estampado)

### Takeaway
As fontes de estilo não fixam um número máximo, mas dão duas regras operacionais: padrões do **mesmo tipo** precisam de **escalas bem diferentes**; padrões de **tipos diferentes** convivem com **escala semelhante**; lisos são a base. Para um recomendador casual com poucos atributos, o seguro é 0–1 peça estampada sem penalidade, 2 com condição e 3+ penalizado.

### Cited Findings
- [OPI] Dois padrões do mesmo desenho (listra com listra, xadrez com xadrez): as escalas devem ser "as different as possible" para evitar vibração visual; dois padrões de desenhos diferentes (listra com xadrez): escalas semelhantes, exceto padrões muito miúdos — [Derek Guy, Put This On, 2012](https://putthison.com/?p=17238)
- [OPI] Três padrões do mesmo desenho: variar as três escalas, da menor (camisa) para a maior (gravata), de dentro para fora; o princípio geral é que as peças contrastem e ao mesmo tempo harmonizem — [Put This On](https://putthison.com/?p=17238)
- [OPI] Não há máximo rígido, mas mistura intensa "is more in the realm of eccentric style"; o texto cita quem usa bem quatro ou cinco padrões e quem costuma ficar em um ou dois — [Put This On](https://putthison.com/?p=17238)
- [OPI] Regra central do RMRS: nada de padrões "of a similar size and type"; mesmo tipo em tamanhos diferentes funciona (risca de giz + camisa bengal stripe), tipos diferentes também — [RMRS, matching patterns](https://www.realmenrealstyle.com/matching-patterns-men/)
- [OPI] Lisos devem ser a base do guarda-roupa; duas peças com mesmo padrão e mesma cor ficam "boring and amateurish"; calças estampadas são desaconselhadas (as pernas em movimento fazem o padrão "se mexer"); começar por acessórios estampados; amarrar as cores usando uma peça multicolorida e fazendo o resto repetir ao menos uma de suas cores — [RMRS, matching patterns](https://www.realmenrealstyle.com/matching-patterns-men/)
- [OPI] Padrões discretos (risca de giz, espinha de peixe) acrescentam complexidade sem acrescentar matizes — [RMRS, 3 color outfits](https://www.realmenrealstyle.com/3-color-outfits/)
- [PRE] Penalidade implementada para excesso de peças "statement": 0,1·(n_statement − 1) — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)

### Inferences
- Tabela de score de padrão sugerida (peças grandes: top, bottom, outer), com atributos `pattern_type ∈ {solid, stripe, check/plaid, print, micro}` e, se existir, `pattern_scale ∈ {small, medium, large}`:
  - 0 estampadas (tudo liso): 0,9–1,0 (neutro; opcionalmente 0,9 para não favorecer sempre o look mais sem graça — a variedade pode vir de textura).
  - 1 estampada + restante liso: 1,0.
  - 2 estampadas, tipos diferentes: 0,7; mesmo tipo com escalas diferentes: 0,7; mesmo tipo e mesma escala (ou escala desconhecida): 0,3.
  - 3+ estampadas: 0,2–0,3.
  - Bottom estampado + top estampado: aplicar o menor valor da faixa (RMRS desaconselha calça estampada).
  - Bônus +0,1 se a peça estampada contém a cor de outra peça do look ("color linking").
- Sem atributo de escala no cadastro, a regra "mesmo tipo → penalizar" é o proxy mais seguro; `micro`/textura (espinha de peixe, risca fina) pode ser tratada como liso.
- Padrão deve reduzir o limite de cores: uma estampa multicolorida já consome o "orçamento" de 2 cores não neutras.

### Gaps
- Nenhuma fonte dá um limite numérico de consenso ("no máximo 2 padrões"); o corte em 2 é inferência conservadora para contexto casual/universitário.
- As regras encontradas são centradas em alfaiataria (terno/camisa/gravata); não achei guia específico para estampas casuais (camisa florida, camiseta gráfica, camuflado).
- Sem evidência empírica (estudos com avaliadores) sobre mistura de padrões em roupas.

## 6. Coerência de formalidade (dress codes) e modelagem de clima/conforto térmico (clo, limiares em °C; Cuiabá 35–40 °C)

### Takeaway
A formalidade pode ser modelada como escala ordinal por peça com penalidade pela amplitude dentro do look e matriz de peças permitidas/proibidas por dress code. Para o clima, a unidade padrão é o **clo** (somável por peça); o modelo dinâmico de Schiavon & Lee dá o clo típico em função da temperatura externa, mas satura em 0,46 clo a partir de 26 °C — ou seja, em Cuiabá o alvo é sempre o mínimo (~0,3–0,5 clo) e o que discrimina looks é quanto cada um **excede** esse alvo.

### Cited Findings
**Formalidade**
- [OPI] Ordem de formalidade: Casual < Smart Casual < Business Casual < Dress Casual < Business Professional < Black Tie — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Casual (linha de base): camiseta, jeans, tênis. Business professional: terno, gravata, sapato social — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Smart casual: jeans índigo escuro sem rasgos, chino ou calça de lã cinco-bolsos; polo de malha, henley/crewneck de merino, flanela, chambray ou OCBD; jaqueta opcional (couro, trucker jeans, cardigã); gravata quase nunca; tênis de couro limpo (branco aceito), loafers, chukka de camurça, chelsea; proibidos tênis esportivos, bermuda cargo e camiseta gráfica; regra: um elemento do look deve ser "elevated" — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Business casual: adequado ao escritório sem terno; chino ou calça de lã, camisa com colarinho (ou polo de qualidade), loafers/derbies/chukkas, cinto; paletó opcional; jeans escuro só em alguns escritórios; proibidos tênis, camisetas, roupa esportiva, peças amassadas ou com slogan — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Dress casual: um degrau abaixo do terno; blazer/sport coat quase sempre; calça de lã, jeans nunca; camisa social por dentro; sapato de couro, tênis nunca. Bermudas ficam fora dos três códigos intermediários, mesmo no verão — [RMRS, dress codes](https://www.realmenrealstyle.com/business-casual-vs-smart-casual-vs-dress-casual/)
- [OPI] Preto e marrom convivem quando as peças harmonizam em intensidade e **formalidade** — [Gentleman's Gazette, 11 bad rules](https://www.gentlemansgazette.com/11-bad-mens-style-rules-to-ignore/)
- [PRE] Penalidade de formalidade implementada: níveis ℓ ∈ {0,1,2} por item e `P_form = 0.2·max(0, Δℓ − 1)` (só pune diferença maior que 1 nível); 0,15 de penalidade quando as ocasiões dos itens não se sobrepõem — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)

**Clima / conforto térmico**
- Definição: 1 clo = 0,155 m²·K/W; é o isolamento que mantém uma pessoa em repouso em equilíbrio térmico a 21 °C, com ar a 0,1 m/s — [Wikipedia, Clothing insulation (citando ASHRAE 55-2010 e ASHRAE Fundamentals)](https://en.wikipedia.org/wiki/Clothing_insulation)
- Valores por peça (clo): T-shirt 0,08; camisa social manga curta 0,19; polo/malha esportiva manga curta 0,17; camisa social manga longa 0,25; flanela ou moletom manga longa 0,34; bermuda (walking shorts) 0,08; calça reta fina 0,15 / grossa 0,24; calça de moletom 0,28; suéter manga longa fino 0,25 / grosso 0,36; paletó simples fino 0,36 / grosso 0,44; cueca 0,04; meia de cano curto 0,02 / até a panturrilha 0,03; sapato 0,02; sandália 0,02; bota 0,10 — [Wikipedia, Clothing insulation](https://en.wikipedia.org/wiki/Clothing_insulation)
- Conjuntos típicos (clo): bermuda + camisa manga curta 0,36; calça + camisa manga curta 0,57; calça + camisa manga longa 0,61; calça + camisa manga longa + suéter + T-shirt 1,01; o mesmo + paletó + ceroula 1,30; moletom completo 0,74. O clo do conjunto é obtido somando os valores das peças — [Wikipedia, Clothing insulation](https://en.wikipedia.org/wiki/Clothing_insulation)
- [EMP] Modelo dinâmico de Schiavon & Lee (versão por partes formulada para uso em normas de conforto térmico), com t = temperatura do ar externo às 6h (°C): `I_cl = 1,00` se t < −5; `0,818 − 0,0364·t` se −5 ≤ t < 5; `10^(−0,1635 − 0,0066·t)` se 5 ≤ t < 26; `0,46` se t ≥ 26. Variante com temperatura operativa interna: `I_cl = 10^(0,2134 − 0,0063·t − 0,0165·t_op)`. Ajustado sobre 6.333 observações das bases ASHRAE RP-884 e RP-921 — [Lee & Schiavon 2014, Energies 7(4):1917](https://mdpi.com/1996-1073/7/4/1917)
- As normas de conforto costumam usar valores fixos de 0,5 clo no verão e 1,0 clo no inverno — [Lee & Schiavon 2014, Energies](https://mdpi.com/1996-1073/7/4/1917)
- [PRE] Os dois recomendadores por regras encontrados usam clima só de forma categórica: um consulta a Open-Meteo (temperatura, vento, precipitação) e mapeia para rótulos como "cold", "hot", "windy" sem limiares numéricos — [Kazarian et al. 2025](https://heraldts.khmnu.edu.ua/index.php/heraldts/article/download/1962/1879/6445); o outro descreve adaptações do tipo "rain avoids suede, cold forces layers", também sem faixas de temperatura e sem avaliação — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)

### Inferences
- **Formalidade:** atribuir a cada peça um nível ordinal (ex.: 0 casual … 4 business formal) e a cada ocasião um intervalo aceito. Score = 1 − a·|nível médio do look − alvo da ocasião| − b·max(0, amplitude interna − 1). O "−1" segue o Loom (um degrau de diferença é tolerado: é o "high-low" do smart casual). Além disso, lista de vetos por dress code a partir da matriz do RMRS (ex.: business casual veta tênis esportivo, camiseta, bermuda; dress casual veta jeans e tênis).
- **Adaptação brasileira (minha):** os guias são anglo-americanos; em Cuiabá o "business casual" real tende a dispensar paletó. Tratar paletó/blazer como opcional em todos os códigos até business casual e deixar o veto térmico (abaixo) prevalecer.
- **Clima via clo (cálculo próprio com as fórmulas citadas):** alvo de clo por temperatura das 6h — −5 °C: 1,00; 0 °C: 0,82; 5 °C: 0,64; 10 °C: 0,59; 15 °C: 0,55; 20 °C: 0,51; 25 °C: 0,47; ≥26 °C: 0,46. O modelo foi ajustado em ocupantes de edifícios (escritórios), então descreve o que as pessoas vestem para ambientes internos; ao ar livre em 35–40 °C o confortável fica abaixo disso.
  - `clo_look = Σ clo das peças` (incluir ~0,04 de roupa íntima + 0,02–0,05 de calçado/meia). Exemplos pela tabela: T-shirt + bermuda + sandália ≈ 0,22–0,25; T-shirt + calça fina + tênis ≈ 0,31–0,35; camisa manga longa + calça grossa + sapato ≈ 0,58; com paletó fino ≈ 0,94.
  - `score_clima = clamp(1 − k·max(0, clo_look − clo_alvo(T)) − k_frio·max(0, clo_alvo(T) − clo_look), 0, 1)`, com k ≈ 2–3 (excesso de roupa no calor) e k_frio menor em Cuiabá.
  - Para T ≥ 30 °C, usar alvo ≈ 0,30–0,36 (bermuda + manga curta = 0,36 na tabela ASHRAE) e **veto** de camada externa (paletó, suéter, moletom: +0,25 a +0,44 clo cada) salvo ocasião formal com ar-condicionado; para T ≥ 35 °C penalizar manga longa e calça grossa. Esses cortes de 30/35 °C são sugestão minha, não constam das fontes.
  - Conflito formalidade × calor: um look business formal (~0,9–1,0 clo) viola o alvo térmico em ~0,5 clo; como ocasião pesa 0,30 e clima 0,25, o sistema ainda deve preferir, dentro do nível de formalidade exigido, as peças de menor clo (calça fina 0,15 vs grossa 0,24; camisa manga curta 0,19 vs longa 0,25).
- Chuva/vento (dados disponíveis na Open-Meteo, usada por Kazarian et al.) podem ser regras booleanas separadas (ex.: evitar camurça e tecido claro em chuva), fora do clo.

### Gaps
- ISO 9920 e o texto da ASHRAE 55 não foram consultados diretamente (pagos); os valores de clo vêm da Wikipedia, que cita ASHRAE 55-2010 e o ASHRAE Handbook. A fórmula de soma alternativa `I_cl = 0,835·Σ I_clu + 0,161` (que conheço da literatura ASHRAE antiga) não foi verificada nesta sessão.
- O artigo original Schiavon & Lee (Building and Environment 59:250–260) não foi aberto; as equações vêm de artigo posterior dos mesmos autores na Energies. Link do original para conferência: https://escholarship.org/uc/item/3338m9qf
- Não encontrei fonte revisada por pares com limiares de camadas em °C para uso **externo** em clima tropical, nem dados de clo/umidade específicos para Cuiabá; a faixa 35–40 °C veio do enunciado da tarefa. Umidade, radiação solar e cor do tecido (claro vs. escuro ao sol) não são cobertos pelo clo.
- Não há fonte para dress codes no contexto brasileiro/universitário.

## 7. Diversidade no top-K: MMR, DPP, intra-list diversity — formulação, λ sensato e efeito sobre Hit Rate@K

### Takeaway
Para K=3, o MMR guloso é suficiente: escolher iterativamente o look que maximiza λ·score − (1−λ)·(máxima similaridade com os já escolhidos), com λ ≈ 0,7 como ponto de partida. A evidência (Ziegler et al.) é que diversificar reduz precisão/recall offline, mas aumenta a satisfação do usuário até um nível moderado de diversificação (30–40%); DPP é desnecessário nessa escala.

### Cited Findings
- **MMR (Carbonell & Goldstein, SIGIR 1998).** Componentes: R = lista ranqueada, S = itens já selecionados, Sim1 = relevância em relação à consulta, Sim2 = similaridade entre itens. Forma padrão: `MMR = argmax_{D_i ∈ R\S} [ λ·Sim1(D_i, Q) − (1−λ)·max_{D_j ∈ S} Sim2(D_i, D_j) ]`. Com λ=1 o método devolve o ranking padrão por relevância; com λ=0, um ranking de diversidade máxima; valores intermediários otimizam a combinação linear — [Carbonell & Goldstein 1998](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf) (o texto extraído do PDF veio truncado na fórmula; a expressão acima é a forma padrão, consistente com o fragmento legível e com as definições do artigo)
- Os autores sugerem começar com λ pequeno (ex.: 0,3) para explorar o espaço e depois usar λ maior (ex.: 0,7) para focar; no estudo-piloto com 5 usuários, 80% escolheram o MMR — [Carbonell & Goldstein 1998](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)
- **Intra-List Distance (ILD):** `ILD(S) = (1/C(|S|,2)) · Σ_{i≠j∈S} d(i,j)` (distância média entre pares da lista); **dispersion:** `disp(S) = min_{i≠j∈S} d(i,j)`. Objetivo guloso estilo MMR usado em recomendação: `F(i) = (1−λ)·rel_u(i) + λ·[f(S∪{i}) − f(S)]` (atenção: aqui λ pesa a diversidade, convenção inversa à do MMR original) — ["A Critical Reexamination of Intra-List Distance and Dispersion", arXiv:2305.13801](https://arxiv.org/pdf/2305.13801)
- Limitação conhecida: otimizar ILD pode selecionar itens quase duplicados, enquanto dispersion pode ignorar pares distantes; os autores propõem um meio-termo (Gaussian ILD) — [arXiv:2305.13801](https://arxiv.org/pdf/2305.13801)
- **Intra-list similarity (ILS)** de Ziegler et al.: soma das similaridades entre todos os pares distintos da lista (dividida por 2); valores maiores = menos diversidade. O algoritmo de topic diversification reordena um top-50 em top-10 misturando o rank de relevância com o rank de dissimilaridade, controlado por Θ_F ∈ [0; 0,9] — [Ziegler et al., WWW 2005](https://archives.iw3c2.org/www2005/proceedings/docs/p22.pdf)
- [EMP] Resultado de Ziegler et al. (2.125 usuários em pesquisa online): diversificar reduziu precision e recall nos dois algoritmos testados, mas a satisfação com a lista de item-based CF subiu e teve pico em Θ_F = 0,4 (com 0,9 ficou abaixo do não diversificado); para user-based CF o efeito foi marginal. Conclusão dos autores: o método é prejudicial à acurácia média, porém melhora a satisfação do usuário com a lista — [Ziegler et al. 2005](https://archives.iw3c2.org/www2005/proceedings/docs/p22.pdf)
- **DPP:** modelo probabilístico de repulsão entre itens; a inferência MAP é NP-difícil e Chen et al. propõem um guloso rápido que entrega melhor trade-off relevância–diversidade em datasets públicos e em teste A/B — [Chen, Zhang & Zhou 2018, arXiv:1709.05135](https://arxiv.org/abs/1709.05135)

### Inferences
- **Receita para o StyleUp (K=3):** (1) gerar os N melhores looks pelo score (ex.: N=30–50); (2) look 1 = maior score; (3) looks 2 e 3 por MMR com `sim(a,b) = 0.6·Jaccard(itens de a, itens de b) + 0.4·sim_cor(a,b)` (ou simplesmente nº de peças compartilhadas / nº de slots); (4) λ = 0,7 inicial (relevância dominante), testar 0,5–0,8. Ziegler indica ótimo com 30–40% de peso em diversidade, o que corresponde aproximadamente a λ ≈ 0,6–0,7 na convenção do MMR — mas lá a mistura é de ranks, não de scores, então a equivalência é só aproximada.
- Com K=3, o problema clássico do ILD (quase duplicatas) é real: três looks que trocam só o sapato têm ILD > 0, mas parecem iguais. Usar restrição tipo dispersion: **dois looks do top-3 não podem compartilhar top e bottom ao mesmo tempo** (ou devem diferir em ≥ 2 de 3 slots principais).
- Não misturar conceitos: o critério "variedade 0,10" do score do look (não repetir peças usadas recentemente) é **novidade temporal**; diversidade intra-lista deve entrar só no re-ranking (MMR), senão é contada duas vezes.
- **Efeito em HR@K:** HR@3 só exige 1 acerto entre 3; se os três looks forem quase iguais, os acertos são altamente correlacionados (ou os três agradam ou nenhum). Diversificar descorrelaciona as apostas e tende a **aumentar HR@3** mesmo reduzindo P@3 (looks 2 e 3 têm score menor). Isso é raciocínio probabilístico meu, coerente com o resultado de Ziegler (precisão cai, satisfação sobe), mas não medido em nenhuma fonte recuperada. Reportar HR@3, P@3 e ILD/dispersion juntos e, se possível, comparar λ=1 (sem MMR) vs λ=0,7 no estudo.
- DPP só se justifica com centenas de candidatos e K grande; para K=3 o MMR guloso é equivalente na prática e mais fácil de explicar.

### Gaps
- Não encontrei estudo que meça diretamente o efeito de MMR/diversificação sobre **Hit Rate@K** (as fontes reportam precision/recall e satisfação). Referências que conheço sobre "otimizar a probabilidade de ao menos um item relevante" (ex.: Chen & Karger 2006) não foram verificadas nesta sessão.
- Nenhuma fonte dá λ "ótimo" universal; os valores 0,3/0,7 de Carbonell & Goldstein são exemplos, e o estudo deles tinha 5 usuários.
- Não há referência de diversidade específica para recomendação de outfits a partir de guarda-roupa pequeno (onde a repetição de peças é inevitável).

## 8. Definições citáveis de Hit Rate@K e Precision@K e como calculá-las em estudo pequeno (10 usuários × 5 consultas × 3 looks)

### Takeaway
HitRate@K(u) = 1 se houver ao menos um item relevante entre os K recomendados (0 caso contrário); Precision@K(u) = nº de relevantes entre os K, dividido por K; ambos são médias sobre usuários/listas. No estudo do StyleUp: HR@3 = listas com ≥1 like / 50 e P@3 = likes / 150, sempre com intervalo de confiança, porque n é pequeno.

### Cited Findings
- Definição formal: `HitRate@k(u) = 𝟙[ |rel(u) ∩ rec_k(u)| > 0 ]` — vale 1 se pelo menos um item da lista recomendada é relevante e 0 caso contrário — [Tamm, Damdinov & Vasilev, "Quality Metrics in Recommender Systems: Do We Calculate Metrics Consistently?" (RecSys 2021), arXiv:2206.12858](https://arxiv.org/pdf/2206.12858)
- Definição formal: `Precision@k(u) = |rel(u) ∩ rec_k(u)| / k` — o denominador é sempre o corte k — [arXiv:2206.12858](https://arxiv.org/pdf/2206.12858)
- Inconsistências documentadas: uma biblioteca ("DL RS Evaluation") reporta HitRate = 1,15, fora de [0,1], porque calcula o número médio de itens acertados (k × precision); alguns artigos definem `HR@K = #hits@K / |GT|`, que na prática é Recall; Beta RecSys, OpenRec e MS Recommenders não reportam HitRate; Precision e Recall foram as únicas métricas que coincidiram em todas as bibliotecas testadas — [arXiv:2206.12858](https://arxiv.org/pdf/2206.12858)
- Intervalo para proporções com poucas observações: limite inferior do intervalo de Wilson para um parâmetro de Bernoulli, `(p̂ + z²/(2n) − z·sqrt((p̂(1−p̂) + z²/(4n))/n)) / (1 + z²/n)`, com z = 1,96 para 95% — [Evan Miller, "How Not To Sort By Average Rating"](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html)

### Inferences
- **Operacionalização no estudo (10 usuários × 5 consultas × 3 looks):** unidade de avaliação = lista (usuário, consulta); "relevante" = look marcado com like.
  - `HR@3 = (1/50)·Σ_listas 𝟙[likes_na_lista ≥ 1]`
  - `P@3 = (1/50)·Σ_listas (likes_na_lista / 3) = total_de_likes / 150`
  - Declarar explicitamente no relatório a definição binária de HR (citando o artigo acima), porque há definições divergentes na literatura.
  - Se alguma consulta devolver menos de 3 looks (guarda-roupa pequeno), manter k=3 no denominador de P@3 (definição padrão) e reportar quantas listas ficaram incompletas.
- **Incerteza (cálculo próprio):** com n=50 listas e HR@3 observado de 0,80, o IC de Wilson a 95% é ≈ [0,67; 0,89] (±11 p.p.). Com 150 julgamentos e P@3 = 0,60, erro-padrão ≈ 0,04 (±8 p.p.) ignorando agrupamento. Como as 5 listas de um mesmo usuário são correlacionadas, o n efetivo é menor: reportar também a média por usuário (10 valores) com bootstrap por usuário.
- **Linha de base:** HR@3 é fácil de inflar — se cada look tivesse probabilidade independente p de like, HR@3 = 1 − (1−p)³ (p=0,5 → 0,875; p=0,3 → 0,66). Comparar com um baseline (looks válidos aleatórios, ou o score antigo de cor) na mesma sessão, de preferência com ordem cega/intercalada.
- Em estudo com usuários não há conjunto de verdade fora dos itens mostrados, então Recall@K e NDCG com relevância completa não são bem definidos; HR@3 e P@3 são as métricas adequadas (opcionalmente MRR = posição do primeiro like).

### Gaps
- Não consultei a documentação de RecBole, Microsoft Recommenders ou TorchMetrics diretamente; as definições vêm do artigo que compara essas bibliotecas.
- Não encontrei referência específica sobre tamanho amostral mínimo para HR@K em estudos com usuários; os intervalos acima são cálculo binomial padrão.

## 9. Esquemas simples e robustos de aprendizado online para adaptar os 5 pesos a partir de like/dislike, e armadilhas com poucas amostras

### Takeaway
Com ~15 feedbacks por usuário, o esquema mais defensável é: pesos padrão como prior forte, atualização multiplicativa (Hedge) ou regressão logística regularizada em direção ao prior, limites mínimo/máximo por peso e taxas de aprovação por categoria suavizadas (Beta/Laplace ou limite inferior de Wilson). As fontes recuperadas sustentam a necessidade de personalização e de suavização para n pequeno; as fórmulas de atualização em si vêm da literatura clássica de online learning, que só pude verificar parcialmente.

### Cited Findings
- O método de multiplicative weights é um meta-algoritmo que mantém uma distribuição sobre um conjunto e a ajusta iterativamente com regra de atualização multiplicativa; diversos algoritmos de áreas distintas são instâncias dele e a análise usa uma função potencial exponencial — [Arora, Hazan & Kale, "The Multiplicative Weights Update Method: a Meta-Algorithm and Applications", Theory of Computing 8 (2012), pp. 121–164](https://mirror.theoryofcomputing.org/articles/v008a006/)
- Problema de n pequeno em taxas de aprovação: ordenar por (positivos − negativos) ou por positivos/total dá resultados errados quando há poucas avaliações; a solução proposta é ordenar pelo limite inferior do intervalo de Wilson, que equilibra a proporção observada com a incerteza da amostra pequena (z = 1,96 para 95%) — [Evan Miller](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html)
- [EMP] Gosto por cor é fortemente individual: concordância geral entre usuários de 52%, subindo para 81% dentro de clusters; um modelo personalizado com 20 avaliações do usuário reduziu o erro em cerca de 30% frente a um modelo único — [O'Donovan et al. 2011](https://www.dgp.toronto.edu/~donovan/color/colorcomp.pdf)
- [EMP] Julgamentos de harmonia são mais consensuais (r médio entre observadores +0,51) do que os de preferência (+0,36) — [Schloss & Palmer 2011](https://palmerlab.berkeley.edu/pdf/Schloss&Palmer%282011%29.pdf)
- [PRE] Em um sistema por regras, remover uma penalidade manual melhorou o resultado, sinal de que constantes escolhidas à mão podem estar mal calibradas e precisam de ablação — [Loom, arXiv:2605.09830](https://arxiv.org/abs/2605.09830)

### Inferences
(Formulações padrão de online learning, escritas de memória; conferir em Arora et al. 2012 ou em Cesa-Bianchi & Lugosi, "Prediction, Learning, and Games", antes de citar formalmente.)
- **A. Hedge / multiplicative weights sobre os 5 critérios.** Tratar cada critério c como "especialista" cujo sub-score s_c ∈ [0,1] é a previsão de like. Perda: `ℓ_c = 1 − s_c` se like; `ℓ_c = s_c` se dislike. Atualização: `w_c ← w_c · exp(−η·ℓ_c)`; renormalizar para Σw = 1. Regra clássica: η ≈ sqrt(ln N / T); com N=5 e T=15–50 feedbacks, η ≈ 0,18–0,33. Na prática usar η fixo ≈ 0,1–0,2 e:
  - *shrinkage* para o prior: `w ← (1−α)·w + α·w_default`, α ≈ 0,05–0,1 por atualização;
  - *clipping*: 0,05 ≤ w_c ≤ 0,45, para que ocasião e clima nunca sejam zerados;
  - vantagem: nunca gera peso negativo, é monotônico e explicável; desvantagem: quando os 3 looks mostrados têm sub-scores parecidos em um critério, esse critério quase não aprende.
- **B. Regressão logística online (SGD) com prior.** `p(like) = σ(b + Σ_c w_c·s_c)`; passo: `w_c ← w_c + lr·(y − p)·s_c − lr·λ_reg·(w_c − w_default,c)`; projetar em w ≥ 0 e renormalizar. A regularização em direção aos pesos padrão é um MAP com prior gaussiano centrado no default. Usar lr pequeno (0,05–0,1) e λ_reg alto no começo. Risco: com 15 amostras e 5 parâmetros o ajuste é instável; por isso o prior.
- **C. Taxas de aprovação por categoria/cor/peça (critério "estilo aprendido").** Beta-Bernoulli: `p̂ = (likes + m·k) / (n + k)`, com prior m = taxa global (ou 0,5) e força k ≈ 2–5 pseudo-observações (Laplace = m 0,5, k 2). Para ranquear de forma conservadora, usar o limite inferior de Wilson; para explorar, amostrar da Beta (Thompson sampling) em vez de usar a média.
- **D. Bandit leve.** Reservar 1 dos 3 slots para exploração (ε-greedy com ε ≈ 0,1–0,2, ou Thompson sampling sobre as Betas de C) reduz o viés de só receber feedback dos looks que o próprio score já favorece.
- **Armadilhas com poucas amostras:**
  1. *Atribuição de crédito*: um dislike pode se dever a uma única peça, não a um critério; registrar (se possível) o motivo ou usar o feedback também em nível de item (esquema C), e não só de peso.
  2. *Viés de seleção / faixa restrita*: só os top-3 recebem feedback, e neles todos os sub-scores são altos, o que torna os pesos pouco identificáveis.
  3. *Deriva rápida*: 2–3 dislikes seguidos não devem mover um peso mais que alguns pontos; limitar |w_c − w_default,c| ≤ 0,05 até n ≈ 20–30 feedbacks do usuário.
  4. *Global vs. por usuário*: dado o tamanho das diferenças individuais (O'Donovan), aprender offsets por usuário sobre pesos globais (hierárquico simples: w_user = w_global + δ_user encolhido para 0).
  5. *Restrições duras fora do aprendizado*: vetos de ocasião e de clima (seção 6) devem permanecer como filtros; o aprendizado só reordena o que já é válido.
  6. *Avaliação*: testar pesos adaptados vs. fixos com replay dos feedbacks ou dentro do próprio estudo (HR@3/P@3 das últimas consultas vs. das primeiras), ciente de que 5 consultas por usuário mal permitem observar adaptação.
- Como harmonia é mais consensual que preferência, é razoável deixar o peso de **cor** menos elástico (faixa de clipping mais estreita) e concentrar a adaptação em "estilo aprendido" e "variedade".

### Gaps
- O corpo do survey de Arora, Hazan & Kale não pôde ser aberto (só metadados e resumo); a regra `w_i ← w_i(1 − η·m_i)`, a variante exponencial (Hedge), a condição η ≤ 1/2 e o limite de regret O(sqrt(T ln N)) não foram verificados textualmente nesta sessão.
- Não consultei fontes sobre Thompson sampling, bandits contextuais ou regressão logística bayesiana; as recomendações B–D são prática padrão sem citação verificada.
- Não encontrei estudo publicado que adapte pesos de critérios de um recomendador de outfits por regras a partir de like/dislike com poucas dezenas de amostras; não há evidência direta de quanto ganho esperar.
