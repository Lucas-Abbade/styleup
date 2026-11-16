# Visão zero-shot e cor dominante: FashionCLIP + rembg + k-means em CPU (estado em novembro/2026)

Convenções: "(não verificado nesta pesquisa)" = afirmação vinda de conhecimento prévio, sem fonte aberta nesta sessão. "Teste local" = medição/cálculo feito por mim nesta sessão (Pillow 12.3.0, Python). Números de fornecedores (Marqo, ZooClaw) são auto-reportados.

## 1. FashionCLIP: o que o paper e o model card dizem; é o checkpoint 2.0?; modelos abertos mais novos

### Takeaway
O card de `patrickjohncyh/fashion-clip` descreve o FashionCLIP 2.0 (fine-tune do `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`, licença MIT), com F1 macro ponderado zero-shot de apenas 0,62–0,83 em benchmarks públicos, e avisa que o modelo é enviesado para fotos de produto centralizadas em fundo branco. Marqo-FashionSigLIP/Marqo-FashionCLIP (Apache-2.0, ViT-B/16, ~150M parâmetros) superam o FashionCLIP 2.0 nos benchmarks do próprio fornecedor (P@1 categoria→produto 0,758 / 0,734 contra 0,681), mas são métricas de retrieval e ViT-B/16 custa mais CPU que ViT-B/32.

### Cited Findings
- O card registra uma atualização "10/03/23" chamada FashionCLIP 2.0: mesmo desenho ViT-B/32, porém partindo do checkpoint `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`; os autores creditam o ganho ao volume de dados do LAION (cerca de 5x o do CLIP da OpenAI). O FashionCLIP original partia do ViT-B/32 da OpenAI. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- Tabela de F1 macro ponderado zero-shot do card (FMNIST / KAGL / DEEP): OpenAI CLIP 0,66 / 0,63 / 0,45; FashionCLIP 0,74 / 0,67 / 0,48; Laion CLIP 0,78 / 0,71 / 0,58; FashionCLIP 2.0 0,83 / 0,73 / 0,62. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- Dados de treino: catálogo Farfetch em inglês, mais de 800 mil produtos de mais de 3 mil marcas; as imagens são fotos padrão de produto, em fundo branco e sem pessoas; o texto junta os "highlights" (ex.: "stripes", "long sleeves") com a descrição curta. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- Detalhe do paper: 700 mil produtos para treino, 50 mil para validação, 188 categorias; o conjunto TEST tem 20 mil produtos; os encoders projetam em vetores de 512 dimensões. — [Chia et al., Scientific Reports 2022](https://www.nature.com/articles/s41598-022-23052-9)
- Limitações declaradas no card: viés para imagens padrão de produto (centralizadas, fundo branco); legendas longas no treino fazem consultas mais longas tenderem a funcionar melhor que curtas; herda vieses do CLIP; os autores afirmam que não foi desenvolvido para deploy sem estudo no contexto específico. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- Licença MIT; bibliotecas listadas: Transformers, PyTorch, ONNX, Safetensors; o card mostra 0,2B de parâmetros (arredondado); uso sugerido via `pipeline("zero-shot-image-classification", model="patrickjohncyh/fashion-clip")` ou `AutoProcessor` + `AutoModelForZeroShotImageClassification`. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- No paper, a classificação zero-shot usa rótulos simples como entrada de texto (ex.: "shoes", "shirt"), sem template; a métrica é F1 macro ponderado; DEEP (4.000 imagens com pessoas, 50 categorias) é o teste mais distante do domínio de treino; F-MNIST tem resolução muito menor que o treino. — [Chia et al. 2022](https://www.nature.com/articles/s41598-022-23052-9)
- O paper também reporta: o checkpoint de menor loss de validação não foi o que melhor generalizou em zero-shot; vulnerabilidade a ataques tipográficos (texto colado na imagem muda a predição); linear probe sobre embeddings congelados em 47 categorias, com maior ganho no KAGL e queda no F-MNIST; mapas de localização qualitativos para conceitos como "long sleeves". — [Chia et al. 2022](https://www.nature.com/articles/s41598-022-23052-9)
- Marqo-FashionCLIP e Marqo-FashionSigLIP: licença Apache-2.0; cerca de 150M de parâmetros cada; bases ViT-B-16 (LAION) e ViT-B-16-SigLIP-webli; treino com Generalised Contrastive Learning (loss de sete partes: descrições, títulos, cores, materiais, categorias, detalhes, palavras-chave) sobre mais de 1 milhão de produtos. — [Blog Marqo](https://www.marqo.ai/blog/search-model-for-fashion); [HF Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP)
- Benchmark Marqo, categoria→produto (média de 5 datasets), P@1 / MRR: Marqo-FashionSigLIP 0,758 / 0,812; Marqo-FashionCLIP 0,734 / 0,776; ViT-B-16-SigLIP-webli 0,690 / 0,751; FashionCLIP2.0 0,681 / 0,741; ViT-B-16-laion2b 0,673 / 0,743; OpenFashionCLIP 0,653 / 0,720. — [GitHub marqo-FashionCLIP](https://github.com/marqo-ai/marqo-FashionCLIP)
- Benchmark Marqo, subcategoria→produto (4 datasets), P@1 / MRR: Marqo-FashionSigLIP 0,767 / 0,811; Marqo-FashionCLIP 0,747 / 0,772; FashionCLIP2.0 0,676 / 0,733; ViT-B-16-SigLIP 0,643 / 0,726; OpenFashionCLIP 0,619 / 0,689. — [GitHub marqo-FashionCLIP](https://github.com/marqo-ai/marqo-FashionCLIP)
- Benchmark Marqo, texto→imagem (6 datasets), Recall@1 / MRR: Marqo-FashionSigLIP 0,121 / 0,239; Marqo-FashionCLIP 0,094 / 0,200; FashionCLIP2.0 0,077 / 0,165. Datasets de avaliação: DeepFashion In-shop, DeepFashion Multimodal, Fashion200k, KAGL, Atlas, Polyvore, iMaterialist. — [GitHub marqo-FashionCLIP](https://github.com/marqo-ai/marqo-FashionCLIP)
- Ganhos relativos anunciados contra FashionCLIP2.0: +22% / +57% em Recall@1 texto→imagem, +8% / +11% em P@1 categoria→produto, +11% / +13% em P@1 subcategoria→produto (Marqo-FashionCLIP / Marqo-FashionSigLIP); o blog também alega inferência 10% mais rápida que FashionCLIP2.0 e OpenFashionCLIP. — [Blog Marqo](https://www.marqo.ai/blog/search-model-for-fashion)
- Uso do Marqo-FashionSigLIP: `open_clip.create_model_and_transforms('hf-hub:Marqo/marqo-fashionSigLIP')` + `open_clip.get_tokenizer(...)`; ou `AutoModel`/`AutoProcessor` com `trust_remote_code=True` e `get_image_features(..., normalize=True)`; o repositório traz tags ONNX e Transformers.js e duas variantes quantizadas. — [HF Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP)
- Conflito de datas: a página do blog exibe 26/10/2025, mas a citação no GitHub indica agosto de 2024, versão 1.0.0. — [Blog Marqo](https://www.marqo.ai/blog/search-model-for-fashion); [GitHub marqo-FashionCLIP](https://github.com/marqo-ai/marqo-FashionCLIP)
- O card da Marqo menciona um sucessor "Marqo Fashion SigLIP 2" com alegados +78% em MRR/recall sobre o Marqo-FashionSigLIP, sem detalhar baseline na página. — [HF Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP)
- ZooClaw-FashionSigLIP2 (arXiv 2606.27708, Xue e Xu): SigLIP2-base-patch16-384 com fine-tuning completo + destilação (LwF) + WISE-FT (α=0,4); hospedado em `srpone/zooclaw-fashionsiglip2`, carregável por `AutoModel.from_pretrained`; a base aparece com 86M de parâmetros e checkpoint de 1,4 GB; licença não informada no paper; só há métricas de retrieval texto→imagem (ex.: R@1 0,449 contra 0,412 do Marqo-FashionSigLIP no benchmark próprio de consultas longas), nada de classificação zero-shot. — [arXiv 2606.27708](https://arxiv.org/pdf/2606.27708)

### Inferences
- O repositório `patrickjohncyh/fashion-clip` é, pelo card, o FashionCLIP 2.0; não conferi hash/commit dos pesos, mas o benchmark da Marqo trata esse modelo como "FashionCLIP2.0". Vale registrar no código o `revision` (commit) usado.
- F1 de 0,62–0,83 em benchmarks públicos indica que ≥90% em 30 categorias finas com fotos de celular não é garantido só com zero-shot do FashionCLIP 2.0. As alavancas, em ordem de custo: (1) aproximar a imagem do domínio de treino (fundo branco, centralizado — ver seção 3); (2) prompt ensembling e hierarquia (seção 2); (3) trocar para Marqo-FashionSigLIP/Marqo-FashionCLIP; (4) linear probe (regressão logística) sobre embeddings congelados com algumas centenas de fotos rotuladas — o próprio paper usa linear probe e continua 100% CPU.
- Custo em CPU: ViT-B/32 a 224 px processa 49 patches; ViT-B/16 a 224 px, 196; ViT-B/16 a 384 px (ZooClaw/SigLIP2-384), 576. Espera-se o encoder de imagem dos modelos Marqo ~4x mais caro que o do FashionCLIP 2.0 e o do ZooClaw ainda mais (cálculo meu). A alegação "10% mais rápido" da Marqo não bate com essa conta e deve ser medida no laptop alvo.
- As métricas da Marqo são de retrieval (texto de categoria → ranking de produtos), não acurácia de classificação imagem→categoria; a direção do ganho é plausível, o tamanho do ganho precisa ser medido no conjunto rotulado próprio.
- SigLIP é treinado com loss sigmoide; softmax sobre classes continua servindo para ranquear, mas os limiares de confiança (0,45/0,15) não são transferíveis entre modelos.

### Gaps
- Não encontrei acurácia zero-shot publicada para um conjunto de ~30 categorias parecido com o do projeto, nem para fotos de celular de peça única.
- Não verifiquei se "Marqo Fashion SigLIP 2" tem pesos abertos e qual a licença; idem licença do ZooClaw-FashionSigLIP2.
- LookBench (arXiv 2601.14706, benchmark aberto de retrieval de moda) apareceu na busca e não foi lido.
- Tamanho em disco dos checkpoints (FashionCLIP ~600 MB; Marqo ~800 MB) não verificado nesta pesquisa.

## 2. Prompt engineering: ensembling vs. max-over-prompts, templates, hierarquia, calibração e rejeição

### Takeaway
O paper do CLIP sustenta exatamente o desenho novo: média dos embeddings de texto por classe (ensemble no espaço de embeddings, cacheado), que somou +3,5 pontos no ImageNet sobre o prompt único, e quase 5 pontos junto com prompt engineering. Os limiares 0,45/0,15 não têm base publicada: dependem do logit scale, do número de classes e do modelo, e o CLIP zero-shot é reconhecidamente mal calibrado — precisam ser ajustados em dados rotulados.

### Cited Findings
- O template padrão "A photo of a {label}." rendeu +1,3% de acurácia no ImageNet frente ao nome da classe sozinho. — [Radford et al. 2021, seção 3.1.4](https://arxiv.org/pdf/2103.00020)
- Contexto específico do domínio ajuda: "A photo of a {label}, a type of pet." no Oxford-IIIT Pets, indicação de comida/aeronave em Food101/FGVC Aircraft, "a satellite photo of a {label}." em imagens de satélite. — [Radford et al. 2021](https://arxiv.org/pdf/2103.00020)
- O ensemble do CLIP é montado no espaço de embeddings, não no de probabilidades; os embeddings médios são cacheados, de modo que o custo amortizado equivale ao de um classificador único. — [Radford et al. 2021](https://arxiv.org/pdf/2103.00020)
- Com 80 templates no ImageNet, o ganho adicional foi de 3,5% sobre o prompt padrão; somando prompt engineering e ensembling, quase 5%. — [Radford et al. 2021](https://arxiv.org/pdf/2103.00020)
- Polissemia do nome da classe prejudica quando falta contexto (guindaste vs. grou em "crane"; "boxer" como raça de cão ou atleta). — [Radford et al. 2021](https://arxiv.org/pdf/2103.00020)
- Para o FashionCLIP, consultas mais longas e no estilo das legendas Farfetch (highlights + descrição curta) tendem a funcionar melhor que consultas curtas. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- LeVine et al. mostram que a inferência zero-shot do CLIP é mal calibrada e que uma única temperatura aprendida por modelo CLIP generaliza entre datasets e escolhas de prompt. — [arXiv 2303.12748](https://arxiv.org/abs/2303.12748)
- Na configuração do CLIP, `logit_scale_init_value` é 2,6592; o valor efetivo é um parâmetro aprendido do checkpoint. — [Docs transformers CLIP](https://huggingface.co/docs/transformers/main/en/model_doc/clip)

### Inferences
- Um softmax único sobre TODOS os prompts com max por categoria (versão antiga) divide a massa de probabilidade entre prompts quase sinônimos da mesma classe: a probabilidade top-1 cai artificialmente, classes com mais prompts ficam penalizadas e os valores não somam 1 por classe. A média de embeddings por classe elimina isso.
- Atenção à renormalização: a média de 2 embeddings unitários com cosseno 0,8 entre si tem norma √0,9 ≈ 0,949. Sem renormalizar, os logits dessa classe encolhem ~5%; com similaridade ~0,25–0,30 e escala 100, isso tira ~1,3–1,5 de logit (fator ~4 em odds) das classes com 2 prompts em relação às de 1 prompt (cálculo meu). Renormalizar após a média e, de preferência, usar o mesmo número de templates em todas as classes.
- Usar `model.logit_scale.exp()` do checkpoint em vez de 100 fixo; FashionCLIP e SigLIP podem ter escalas diferentes. (O teto de 100 no CLIP original é de memória, não reverificado.)
- Esqueleto recomendado:
  ```python
  def feats(out):  # compatível com transformers 4.x e 5.x
      return out if isinstance(out, torch.Tensor) else out.pooler_output
  with torch.inference_mode():
      t = feats(model.get_text_features(**tok(prompts, padding=True, return_tensors="pt")))
  t = t / t.norm(dim=-1, keepdim=True)
  cls = t.view(n_classes, n_templates, -1).mean(1)
  cls = cls / cls.norm(dim=-1, keepdim=True)          # renormalizar
  probs = (model.logit_scale.exp() * img_emb @ cls.T).softmax(-1)
  ```
- Templates candidatos para fotos de produto (hipótese a validar no conjunto rotulado, 4–8 por classe): "a photo of a {label}, a type of clothing", "a product photo of a {label} on a white background", "a flat lay photo of a {label}", "a studio photo of a {label}", "{label}" puro (como no paper do FashionCLIP) e uma legenda estilo Farfetch ("crew neck, long sleeves, cotton {label}").
- Redação do nome da classe: testar sinônimos EUA/Reino Unido no ensemble ("pants"/"trousers", "sneakers"/"trainers", "sweater"/"jumper", "tank top"/"vest top", "flip-flops"/"thong sandals") e desambiguar termos polissêmicos ("cap" → "baseball cap", "watch" → "wristwatch", "boots" → "ankle boots / leather boots", "belt" → "leather belt"). Pares confundíveis (sneakers vs. leather sneakers, casual vs. dress shirt, chinos vs. dress trousers, sweatshirt vs. sweater) merecem prompts contrastivos com material/detalhe ("white leather low-top sneakers" vs. "mesh running sneakers").
- Hierarquia: primeiro softmax entre ~5 famílias (tops, bottoms, calçados, outerwear, acessórios), depois softmax só entre as irmãs. Reduz confusões absurdas entre famílias e torna os limiares mais estáveis (5–8 classes por softmax). Custo zero em CPU (um produto matricial a mais). Alternativa equivalente: somar probabilidades das filhas para obter a família.
- Atributos: um softmax separado por grupo (manga: sleeveless/short/long; padrão: solid/striped/printed/plaid), com prompts condicionados à categoria prevista ("a long-sleeved {categoria}", "a striped {categoria}"); "highlights" como "stripes" e "long sleeves" faziam parte do texto de treino do FashionCLIP.
- Limiares 0,45/0,15: são um ponto de partida razoável, não um valor defensável a priori. Procedimento: (a) para cada foto rotulada, guardar p_top1, margem e acerto; (b) traçar curva risco×cobertura (classificação seletiva) e escolher o limiar que entrega a acurácia-alvo nos aceitos (ex.: ≥95%) com a maior cobertura; (c) opcionalmente ajustar uma temperatura única por modelo (temperature scaling, como em LeVine et al.) antes de fixar limiares; (d) com 50–100 fotos, usar validação cruzada/bootstrap e manter um conjunto de teste separado, senão os limiares ficam sobreajustados; (e) reajustar sempre que mudar modelo, prompts, número de classes ou pré-processamento.

### Gaps
- Não achei estudo comparando diretamente "max sobre prompts em um softmax" com média de embeddings; a recomendação apoia-se no paper do CLIP e em raciocínio.
- Evidência publicada para classificação zero-shot hierárquica (ex.: CHiLS, ICML 2023) e para classificação seletiva (Geifman e El-Yaniv 2017) e temperature scaling (Guo et al. 2017): citadas de memória, não verificadas nesta pesquisa.
- Nenhuma fonte com templates validados especificamente para FashionCLIP em fotos de celular.

## 3. Fundo branco vs. RGBA/preto; o que o `CLIPImageProcessor` faz com RGBA; remoção de fundo ajuda?

### Takeaway
Compor em branco é a escolha coerente com o domínio de treino do FashionCLIP (fotos de produto em fundo branco, viés declarado no card), e passar RGBA direto gera fundo preto porque o processor apenas chama `image.convert("RGB")`, que descarta o alfa. Não há A/B publicado para esse caso exato: o ganho precisa ser medido no conjunto rotulado.

### Cited Findings
- `convert_to_rgb` do transformers só chama `image.convert("RGB")` para imagens PIL que não estejam em modo RGB; não há composição do alfa sobre fundo algum; entradas não-PIL retornam inalteradas. — [transformers image_transforms.py](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/image_transforms.py)
- Padrões do `CLIPImageProcessor`: `do_convert_rgb=True`, resize com `shortest_edge=224`, `do_center_crop=True` com crop 224x224, normalização com média [0.48145466, 0.4578275, 0.40821073] e desvio [0.26862954, 0.26130258, 0.27577711]. — [Docs transformers CLIP](https://huggingface.co/docs/transformers/main/en/model_doc/clip)
- Teste local (Pillow 12.3.0): `Image.convert("RGB")` em pixel RGBA transparente com RGB zerado devolve (0,0,0); se o RGB oculto for (123,222,111), devolve esse valor; `Image.alpha_composite` sobre branco devolve (255,255,255). Ou seja, o alfa é ignorado e aparece o RGB subjacente (preto no recorte do rembg). — Teste local desta pesquisa; comportamento do processor em [image_transforms.py](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/image_transforms.py)
- O FashionCLIP foi treinado com imagens de produto em fundo branco sem pessoas e o card declara viés para imagens centralizadas em fundo branco. — [HF model card](https://huggingface.co/patrickjohncyh/fashion-clip)
- Em reconhecimento de ações zero-shot baseado em CLIP, mascarar o fundo piorou o desempenho no Kinetics400 (onde o fundo carrega sinal) e melhorou no Mimetics (viés de fundo fraco): o efeito de remover fundo depende de o fundo ser informativo ou distrator. — [Fukuzawa et al., arXiv 2501.12681](https://arxiv.org/abs/2501.12681)
- No transformers v5 o backend padrão do image processor é `torchvision` quando instalado, senão `pil`; `use_fast` foi depreciado em favor de `backend`. — [MIGRATION_GUIDE_V5](https://raw.githubusercontent.com/huggingface/transformers/main/MIGRATION_GUIDE_V5.md)

### Inferences
- Fundo preto é fora de distribuição para o FashionCLIP e ainda cria contorno de alto contraste; fundo branco reproduz o catálogo Farfetch. Espera-se ganho, sobretudo em peças escuras (que somem no preto).
- O center crop corta as bordas de imagens não quadradas: numa foto 768x1024, 12,5% do topo e 12,5% da base são descartados (cálculo a partir dos padrões do processor) — calças, vestidos e casacos longos perdem barra/gola. Recomendação: recortar pelo bounding box da máscara, adicionar margem branca de ~5–10% e fazer pad para quadrado ANTES do processor.
- Para cenas de celular, o fundo (cama, piso, cabide, mão) é distrator, não sinal; remover tende a ajudar. Risco: máscara ruim (peça branca em lençol branco, peças finas, preto sobre sombra) destrói a peça. Mitigação: se a área da máscara for <5% ou >95% da imagem, cair para a foto original; opcionalmente fazer ensemble (média) dos embeddings da foto original e do recorte em branco.
- A/B recomendado no conjunto rotulado, com os mesmos prompts: (1) foto original; (2) recorte em fundo preto; (3) recorte em branco; (4) recorte em branco + crop pelo bbox + pad quadrado; (5) média dos embeddings de 1 e 4. Comparar com teste pareado (mesmas fotos).
- Fixar o `backend` do image processor (pil ou torchvision): a interpolação do resize difere e pode mudar predições limítrofes entre máquinas.

### Gaps
- Nenhum estudo publicado encontrado medindo fundo branco vs. preto vs. original para FashionCLIP/CLIP em peças de roupa.
- ObjectCompose (ACCV 2024), sobre robustez de modelos de visão a trocas de fundo, apareceu na busca e não foi lido.

## 4. Desempenho em CPU: cache de texto, API `get_*_features`, threads, quantização/ONNX, latências

### Takeaway
A maior economia já foi feita (texto codificado uma vez); o risco imediato é de compatibilidade: no transformers v5 `get_image_features`/`get_text_features` passaram a devolver `BaseModelOutputWithPooling`, e o embedding fica em `.pooler_output`. O u2net foi medido em 0,12 s por imagem em CPU de desktop; não achei número publicado confiável para ViT-B/32 em laptop, mas a meta de <5 s tem folga grande.

### Cited Findings
- Guia de migração v5: os quatro helpers `get_text_features`, `get_image_features`, `get_audio_features` e `get_video_features` agora retornam `BaseModelOutputWithPooling` (ou subclasse); para obter o tensor antigo, ler `outputs.pooler_output` (PR #42564). — [MIGRATION_GUIDE_V5](https://raw.githubusercontent.com/huggingface/transformers/main/MIGRATION_GUIDE_V5.md); [PR 42564](https://github.com/huggingface/transformers/pull/42564)
- A documentação atual do `CLIPModel` confirma o tipo de retorno `BaseModelOutputWithPooling` (ou tupla com `return_dict=False`) e usa `torch.inference_mode()` nos exemplos. — [Docs transformers CLIP](https://huggingface.co/docs/transformers/main/en/model_doc/clip)
- Outras mudanças do v5: `dtype` padrão em `from_pretrained` virou `auto` (carrega no dtype salvo); classes `XXXFeatureExtractor` removidas em favor de `XXXImageProcessor`; TensorFlow e Jax removidos. — [Release v5.0.0](https://github.com/huggingface/transformers/releases/tag/v5.0.0); [MIGRATION_GUIDE_V5](https://raw.githubusercontent.com/huggingface/transformers/main/MIGRATION_GUIDE_V5.md)
- Já existe documentação versionada do transformers 5.13.1, ou seja, um `pip install transformers` sem pin em nov/2026 traz a série 5.x. — [Docs transformers v5.13.1](https://huggingface.co/docs/transformers/v5.13.1/model_doc/align.md)
- Cachear os embeddings médios de texto torna o custo do ensemble igual ao de um classificador único. — [Radford et al. 2021](https://arxiv.org/pdf/2103.00020)
- rembg com u2net: mediana de 0,12 s por imagem e pico de 2,1 GB de RAM em AMD Ryzen 7 9700X com 6 vCPUs, sem GPU (rembg 2.0.85, onnxruntime 1.30.0); isnet-general-use: 0,33 s e 2,8 GB; ~2 minutos por 1.000 fotos com u2net. — [creativeainews, 01/10/2026](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/)
- O u2net do rembg normaliza a entrada para 320x320 (média/desvio ImageNet) e reamostra a máscara de volta ao tamanho original com LANCZOS. — [rembg sessions/u2net.py](https://raw.githubusercontent.com/danielgatis/rembg/main/rembg/sessions/u2net.py)
- rembg v2.0.77 passou a aceitar opções de sessão do ONNX Runtime na fábrica de sessões. — [rembg releases](https://github.com/danielgatis/rembg/releases)
- O repositório do FashionCLIP lista ONNX entre as bibliotecas; o do Marqo-FashionSigLIP traz ONNX e duas variantes quantizadas. — [HF FashionCLIP](https://huggingface.co/patrickjohncyh/fashion-clip); [HF Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP)

### Inferences
- Código robusto a 4.x e 5.x: `out = model.get_image_features(pixel_values=px); emb = out if isinstance(out, torch.Tensor) else out.pooler_output`. Sem isso, `out / out.norm(...)` quebra no v5. Alternativa: fixar `transformers<5` ou `>=5` em requirements e testar o shape (512) no startup.
- Com `dtype="auto"` no v5, passar `dtype=torch.float32` explicitamente em CPU (half em CPU é lento/não suportado em várias ops).
- Como o u2net opera em 320x320, redimensionar para 1024 px antes do rembg não melhora a máscara; só encarece I/O, reamostragem LANCZOS e composição. 512–768 px devem bastar para CLIP (224 px) e para cor (a Stitch Fix reduz para 300x200 antes de clusterizar — ver seção 6).
- Orçamento estimado por foto, a quente (estimativa, não medida): decodificar/redimensionar ~50–150 ms; rembg u2net ~0,1–0,5 s; ViT-B/32 imagem ~50–200 ms em PyTorch FP32; k-means em ≤20 mil pixels ~10–50 ms; total bem abaixo de 1,5 s. Os ~4 s anteriores vinham de recodificar todos os prompts 3 vezes por requisição.
- Startup: carregar modelo + codificar ~30 classes × 4–8 templates uma vez (segundos); persistir a matriz de embeddings em `.npy` com chave = hash (modelo + revision + prompts) permite até não carregar a torre de texto em produção.
- Primeira requisição de 128 s: pré-baixar pesos no build/instalação (`huggingface_hub.snapshot_download` + `HF_HUB_OFFLINE=1`; `rembg d u2net`), criar `new_session("u2net")` e o `CLIPModel` no startup e rodar um warm-up com imagem sintética.
- Threads: `torch.set_num_threads(<núcleos físicos>)`; limitar também o ONNX Runtime do rembg (`SessionOptions.intra_op_num_threads`) para evitar oversubscription, já que as duas etapas rodam em sequência no mesmo processo.
- ONNX/quantização: exportar só a torre de visão + projeção para ONNX e rodar no onnxruntime que o rembg já instala permite até remover o PyTorch do runtime (startup e RAM menores). Quantização dinâmica INT8 (`onnxruntime.quantization.quantize_dynamic` ou `torch.ao.quantization.quantize_dynamic` em `nn.Linear`) costuma dar ~1,5–2x em ViT, mas altera similaridades: revalidar acurácia e limiares; só vale se a etapa CLIP for gargalo — provavelmente não é.
- Texto e imagem precisam vir do MESMO checkpoint/precisão: se quantizar a torre de visão, recalibrar limiares.

### Gaps
- Latência publicada e confiável do encoder de imagem ViT-B/32 em CPU de laptop: não encontrada (a página de performance do Apache Beam para `clip-ViT-B-32` só mostra gráficos, sem números legíveis). Medir com `time.perf_counter` em 20 repetições após warm-up.
- Ganho real de quantização dinâmica/ONNX para CLIP ViT-B/32: não verificado; um tópico de fórum intitulado "CLIP model quantized by quanto run slower" apareceu na busca (não lido), sinal de que o ganho não é automático.
- Estado de depreciação de `torch.ao.quantization` nas versões de PyTorch de 2026 e recomendações oficiais de threading do PyTorch/ONNX Runtime: não verificados nesta pesquisa.
- Quais arquivos ONNX existem em `patrickjohncyh/fashion-clip` (modelo completo ou torres separadas): não verificado.

## 5. rembg: qual modelo para fotos de roupa, de onde baixa e como aquecer; alpha matting

### Takeaway
Manter `u2net` (176 MB, Apache-2.0, 0,12 s/imagem) nomeado explicitamente, ou trocar por `isnet-general-use` (179 MB, Apache-2.0, 0,33 s) se as bordas importarem; os dois cabem na meta. Cuidado crítico: desde o rembg v2.0.80 o modelo padrão é `bria-rmbg` (~1 GB, CC BY-NC 4.0, uso comercial exige contrato) e os modelos passaram a ficar em `~/.rembg/models`, com `U2NET_HOME` depreciado.

### Cited Findings
- Modelos listados no README: u2net (uso geral), u2netp (versão leve), u2net_human_seg, u2net_cloth_seg (parsing de roupas em retratos humanos: parte superior, inferior, corpo inteiro), silueta (igual ao u2net, ~43 MB), isnet-general-use, isnet-anime, sam, birefnet-general, birefnet-general-lite, birefnet-portrait, birefnet-dis, birefnet-hrsod, birefnet-cod, birefnet-massive, bria-rmbg (padrão; ~1,02 GB; 1024x1024), birefnet-general-fp16; `withoutbg` e `atlascloud` são backends de API em nuvem (enviam a imagem a terceiros). — [README rembg](https://github.com/danielgatis/rembg)
- O README avisa que o RMBG-2.0 (bria-rmbg) exige acordo pago para uso comercial. — [README rembg](https://github.com/danielgatis/rembg)
- v2.0.80 (17/ago): bria-rmbg vira o modelo padrão, modelos passam a `~/.rembg/models`, entra o refinamento de bordas ViTMatte (`-vm`); v2.0.79: descontaminação de cor opcional para bordas suaves; v2.0.85 (20/set) é a mais recente. A página não mostra o ano; um artigo de 01/10/2026 testa a 2.0.85. — [rembg releases](https://github.com/danielgatis/rembg/releases); [creativeainews](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/)
- Armazenamento: download no primeiro uso para `~/.rembg/models/<modelo>/` (ex.: `~/.rembg/models/u2net/u2net.onnx`); raiz padrão `$XDG_DATA_HOME/rembg` ou `~/.rembg`; `REMBG_HOME` sobrescreve; `U2NET_HOME` está depreciado mas ainda tem precedência quando definido; o diretório legado `~/.u2net` continua sendo lido e `rembg m` migra os arquivos; `MODEL_CHECKSUM_DISABLED=1` desliga a verificação de hash. — [README rembg](https://github.com/danielgatis/rembg)
- O u2net é baixado de `https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx`, com verificação MD5 `60024c5c889badc19c04ad937298a77b`. — [rembg sessions/u2net.py](https://raw.githubusercontent.com/danielgatis/rembg/main/rembg/sessions/u2net.py)
- `rembg d` é o subcomando para baixar modelos antecipadamente; `session = new_session(...)` + `remove(input, session=session)` reutiliza a sessão; instalação CPU: `pip install "rembg[cpu]"`; Python >=3.11 e <3.14. — [README rembg](https://github.com/danielgatis/rembg)
- Medições em CPU (Ryzen 7 9700X, 6 vCPUs, 12 GB RAM), download / pico de RAM / mediana por imagem / licença dos pesos: u2net 176 MB / 2,1 GB / 0,12 s / Apache-2.0; isnet-general-use 179 MB / 2,8 GB / 0,33 s / Apache-2.0; birefnet-general-lite 224 MB / processo morto acima de 6,6 GB / não terminou / MIT; birefnet-general 973 MB / morto acima de 6,9 GB / MIT; bria-rmbg 1.024 MB / morto acima de 6,9 GB / CC BY-NC 4.0. — [creativeainews](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/)
- Qualidade no AIM-500 (500 fotos): IoU médio 0,859 (u2net) vs. 0,876 (ISNet); recortes limpos (IoU ≥0,95) 281 vs. 300; falhas (IoU <0,5) 45 vs. 36; erro na faixa de borda 15,9% vs. 12,8%; SAD mediano praticamente empatado (24,5 vs. 25,1). — [creativeainews](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/)
- Modos de borda (subconjunto de 150 fotos): alpha matting `-a` soma 1,3–1,5 s por imagem e reduz o erro de borda do u2net de 16,7% para 14,9%; ViTMatte `-vm` soma 1,3 s e leva a 12,6%; `-ppm` (máscara binária) piorou o erro por pixel em 150/150 fotos com u2net. — [creativeainews](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/)
- O README descreve o alpha matting como solver de forma fechada, lento e sujeito a não convergir (com fallback para recorte descontaminado). — [README rembg](https://github.com/danielgatis/rembg)

### Inferences
- `remove(img)` ou `new_session()` sem nome, em rembg ≥2.0.80, baixa ~1 GB de um modelo não comercial que nem coube em 6,9 GB de RAM no teste citado: sempre passar `"u2net"` (ou `"isnet-general-use"`) e fixar a versão do rembg.
- Como `U2NET_HOME` ainda tem precedência mas está depreciado, definir `REMBG_HOME` (e, por compatibilidade, o mesmo caminho em `U2NET_HOME` só se necessário) e empacotar o `.onnx` no instalador/imagem; warm-up com `new_session("u2net")` no startup.
- `u2net_cloth_seg` foi feito para roupas vestidas em pessoas (parsing em 3 partes); para peça única em flat lay/cabide o modelo certo é um de saliência geral (u2net/isnet).
- Alpha matting/ViTMatte (+1,3 s) não compensa aqui: o CLIP reduz para 224 px e a cor usa máscara erodida, então bordas finas não importam. Evitar `-ppm` não é crítico para cor (a erosão descarta a borda), mas também não ajuda.
- BiRefNet e BRIA entregam bordas melhores em GPU, porém em CPU de laptop com 8–16 GB são inviáveis ou lentos; BRIA ainda viola a exigência de licença aberta para uso comercial.
- Uso de RAM: ~2 GB de pico do u2net + PyTorch/CLIP (~1 GB) cabe em laptop de 8 GB, com folga pequena; ISNet sobe para ~2,8 GB.

### Gaps
- Nenhum benchmark específico de recorte de roupas (flat lay, cabide, peça branca em fundo claro) entre modelos do rembg; o AIM-500 é de matting genérico. O artigo citado é de autor único (medições próprias, fonte secundária).
- u2netp e silueta não foram medidos na fonte; tempos de BiRefNet-lite em CPU com mais RAM desconhecidos.
- Papers de U²-Net, IS-Net (DIS) e BiRefNet não foram consultados nesta sessão; licenças dos pesos vêm do artigo secundário e do README.
- Nomes exatos dos parâmetros Python de alpha matting (`alpha_matting_foreground_threshold` etc.) e de `post_process_mask`: não constam na página lida do README (não verificado).

## 6. Extração da cor dominante: espaço de cor, sombras/halo, escolha do cluster, estampas, balanço de branco

### Takeaway
O melhor relato de engenharia encontrado (Stitch Fix) clusteriza em CIELAB com K adaptativo (K=8, reduzindo enquanto houver cluster com menos de 3% dos pontos), avalia a cor principal por CIEDE2000 (média 5,86 em ~1.000 imagens) e admite que sombras continuam sem solução. Para o pipeline atual: trocar RGB por CIELAB, manter a erosão da máscara, fundir clusters próximos e reportar segunda cor em peças estampadas.

### Cited Findings
- Pipeline da Stitch Fix: imagem com cor corrigida, reduzida a 300x200 e convertida para CIELAB; superpixels Quickshift (de ~60 mil pixels para algumas centenas); fusão de regiões vizinhas com diferença de cor abaixo de 10 (~100 regiões); remoção só de fundo branco (L > 99 e a, b entre -0,5 e 0,5); k-means em (L, a, b) com K=8, repetindo com K menor sempre que algum cluster tiver menos de 3% dos pontos; saída de 1 a 8 centros com a fração de pontos de cada um. — [Stitch Fix, What Color Is This? Part 2](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)
- Avaliação da Stitch Fix: ~1.000 imagens com a cor principal marcada à mão; CIEDE2000 médio de 5,86 para a cor principal (7,82 em CIE76, pouco mais de 3 diferenças apenas perceptíveis); erro absoluto médio de 2,28 na contagem de cores. — [Stitch Fix](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)
- Problemas relatados: sombras seguem sem solução (deduplicar por matiz falhou porque a sombra não altera a cor de forma consistente); sapatos mostram o interior; joias são pequenas demais; xadrez funcionou porque os superpixels agrupam linhas da mesma cor; SLIC teve dificuldade com listras. — [Stitch Fix](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)
- Alternativas testadas pela Stitch Fix: colorgram.py (hash de pixels, <1 s por imagem, porém maior distância na cor principal); gap statistic reduziu o erro de contagem mas piorou a cor principal; silhouette exige ≥2 clusters e falha em peças de uma cor; DBSCAN teve resultado fraco. — [Stitch Fix](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)
- A faixa de borda dos recortes do rembg tem erro de 12–17% dos pixels (u2net 15,9%, ISNet 12,8% no AIM-500), e o rembg ganhou descontaminação de cor para bordas suaves na v2.0.79. — [creativeainews](https://www.creativeainews.com/articles/rembg-background-removal-models-tested-2026/); [rembg releases](https://github.com/danielgatis/rembg/releases)

### Inferences
- Trocar k-means RGB por CIELAB (`skimage.color.rgb2lab` ou `cv2.cvtColor(..., COLOR_RGB2LAB)` com float): distâncias euclidianas em LAB aproximam diferença percebida; em RGB, sombra e cor-base da mesma peça se separam em clusters distintos com facilidade.
- K=4 fixo é pouco para estampas e muito para lisas. Usar K=5–8 com a regra da Stitch Fix (descartar/reduzir enquanto houver cluster <3%) e depois fundir centros com ΔE00 < ~8–10; a cor dominante é o maior cluster após a fusão.
- Sombras/brilhos: antes do k-means, descartar os percentis extremos de L* (ex.: 5% mais escuros e 2% mais claros) dentro da máscara; ao fundir, tratar clusters com mesmo matiz/croma e L* menor como sombra do cluster principal. Em peças pretas/brancas (croma baixo) não aplicar o corte de L*.
- "Maior cluster" vs. "ponderado por saturação": o maior cluster é o padrão seguro para a cor-base; ponderar por saturação favorece a cor da estampa/logo e erra em peças neutras (camiseta branca com estampa vermelha viraria "vermelho"). Reportar cor-base (maior) e, se o segundo cluster tiver ≥15–20% e ΔE00 > 20, uma cor secundária — e usar isso como sinal auxiliar para o atributo "padrão" (solid vs. striped/printed/plaid).
- Erosão: binarizar alfa > ~200 e erodir ~1–2% do lado do bbox (mínimo 3 px) elimina halo e mistura de fundo; o erro de borda de 12–17% justifica a etapa.
- Custo: amostrar no máximo 10–20 mil pixels da máscara (a Stitch Fix trabalha em 300x200) mantém o k-means em milissegundos.
- Balanço de branco do celular: o recorte perde a referência neutra. Opção barata: quando o fundo original (fora da máscara) for quase neutro e claro (parede/lençol branco), estimar o iluminante pela mediana do fundo e corrigir (von Kries/ganhos por canal) antes de extrair a cor; caso contrário, não corrigir. Orientar o usuário a fotografar com luz natural em superfície clara tende a render mais que qualquer algoritmo.
- Meta ≥85%: como a nomeação é categórica, avaliar por nome em dois níveis (família e tom) e também por ΔE00 contra uma cor de referência marcada à mão, como fez a Stitch Fix.

### Gaps
- Sem comparação quantitativa publicada (encontrada nesta sessão) entre k-means RGB/HSV e CIELAB para roupas; o arXiv 2406.19520 (análise comparativa de modelos de cor para diferença percebida) apareceu na busca e não foi lido.
- Sem evidência medida sobre correção de balanço de branco em fotos de celular de roupas, nem sobre o ganho exato da erosão de máscara.
- Regra de escolha da "cor principal" da Stitch Fix não está explícita no post.

## 7. Nomeação de cores: CIEDE2000 contra paleta curada, XKCD, ISCC-NBS, Berlin & Kay, vocabulário pt-BR

### Takeaway
Substituir limiares HSV por vizinho mais próximo em CIELAB com CIEDE2000 (referência: Sharma, Wu e Dalal 2005, com dados de teste públicos) contra uma paleta curada de ~35–45 cores com nomes pt-BR em dois níveis (família básica + tom de moda). A lista do XKCD (954 nomes, CC0) fornece âncoras hex verificáveis; não encontrei fonte normativa para o vocabulário de moda brasileiro.

### Cited Findings
- Referência do CIEDE2000: G. Sharma, W. Wu, E. N. Dalal, "The CIEDE2000 Color-Difference Formula: Implementation Notes, Supplementary Test Data, and Mathematical Observations", Color Research and Application, vol. 30, n. 1, p. 21–30, fev. 2005; a página dos autores oferece arquivo de dados de teste (pares L*a*b* e ΔE00 esperado), implementação MATLAB e planilha Excel, e o artigo aponta descontinuidades na fórmula. — [Página de G. Sharma](https://hajim.rochester.edu/ece/sites/gsharma/ciede2000/)
- XKCD color survey: 222.500 sessões de usuário, mais de 5 milhões de cores nomeadas, lista final de 954 nomes com RGB no ponto de maior frequência de cada nome; o autor adverte que monitores variam e que RGB não é um espaço absoluto. — [Blog xkcd](https://blog.xkcd.com/2010/05/03/color-survey-results/)
- O arquivo `rgb.txt` do XKCD declara licença CC0. Âncoras úteis: navy blue #001146, navy #01153e, wine #80013f, wine red #7b0323, burgundy #610023, maroon #650021, khaki #aaa662, olive #6e750e, olive green #677a04, army green #4b5d16, mustard #ceb301, caramel #af6f09, camel #c69f59, tan #d1b26f, charcoal #343837, charcoal grey #3c4142, off white #ffffe4, ivory #ffffcb, cream #ffffc2, sand #e2ca76, beige #e6daa6, terracotta #ca6641, rust #a83c09, brown #653700, dark brown #341c02, salmon #ff796c, coral #fc5a50, lilac #cea2fd, lavender #c79fef, turquoise #06c2ac, teal #029386, denim #3b638c, denim blue #3b5b92, royal blue #0504aa, light blue #95d0fc, baby blue #a2cffe, sky blue #75bbfd, forest green #06470c, dark green #033500, grey #929591, light grey #d8dcd6, dark grey #363737, silver #c5c9c7, gold #dbb40c, pink #ff81c0, hot pink #ff028d, light pink #ffd1df, purple #7e1e9c, violet #9a0eea, red #e50000, orange #f97306, yellow #ffff14, green #15b01a, blue #0343df, black #000000, white #ffffff. — [xkcd rgb.txt](https://xkcd.com/color/rgb.txt)
- A Stitch Fix usa CIEDE2000 como métrica de erro da cor principal e um módulo próprio (Colornamer) para atribuir nomes aos centros de cluster. — [Stitch Fix](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)
- A "Lista de cores" da Wikipédia em português não forneceu valores hex no conteúdo extraído e não lista os tons de moda (marinho, vinho, bordô, cáqui, mostarda, caramelo, grafite, areia, terracota etc.). — [pt.wikipedia Lista de cores](https://pt.wikipedia.org/wiki/Lista_de_cores)

### Inferences
- Paleta pt-BR proposta (mapeamento meu, usando as âncoras XKCD; os hex XKCD são centroides de monitor, mais saturados que tecido real — recalibrar com fotos próprias): marinho → #001146 / #01153e; vinho → #80013f / #7b0323; bordô → #610023 / #650021; cáqui → #aaa662; verde-oliva → #6e750e / #677a04; verde-militar → #4b5d16; mostarda → #ceb301; caramelo → #af6f09 (ou camel #c69f59); grafite → #343837 / #3c4142; off-white → #ffffe4 é amarelado demais, preferir algo como #f5f1e6 (sugestão minha, sem fonte); areia → #e2ca76 (para tecido, algo menos saturado, tipo #d8c9a3, sugestão minha); terracota → #ca6641; bege → #e6daa6; ferrugem → #a83c09; marrom → #653700; jeans → #3b638c; azul-royal → #0504aa; azul-claro → #95d0fc; lilás → #cea2fd; salmão → #ff796c; coral → #fc5a50; turquesa → #06c2ac; cinza → #929591; cinza-claro → #d8dcd6; cinza-escuro → #363737.
- Dois níveis: (1) família básica — preto, branco, cinza, vermelho, laranja, amarelo, verde, azul, roxo, rosa, marrom (os 11 termos básicos de Berlin & Kay, de memória) + bege como neutro de moda; (2) tom de moda. Medir a meta de ≥85% na família e reportar o tom como refinamento; anotadores humanos discordam entre vinho/bordô ou marinho/azul-escuro.
- Várias amostras por nome (3–5 hex por tom, coletados de fotos reais) e 1-NN por ΔE00 funcionam melhor que um protótipo único, porque regiões de nomes não são esféricas em LAB.
- Acromáticos merecem regra explícita antes do 1-NN: croma C* baixo (ex.: < 8–10) → preto / grafite / cinza / cinza-claro / branco / off-white apenas por L* (off-white e bege distinguidos por b* levemente positivo). Limiares a calibrar.
- Preto e marinho, e branco e off-white, são os pares mais sensíveis a exposição e balanço de branco; sinalizar baixa confiança quando ΔE00 entre o 1º e o 2º vizinho for menor que ~3–5.
- Implementação: `skimage.color.deltaE_ciede2000` (ou `colormath`/`colour-science`); validar contra os dados de teste de Sharma. Custo desprezível (1 cor × ~150 protótipos).
- Ambiguidade de "cáqui": no Brasil o termo cobre de bege-amarelado a verde-acinzentado; fixar protótipos e exemplos no guia de anotação.

### Gaps
- Nenhuma fonte aberta e normativa encontrada com hex de referência para o vocabulário de moda pt-BR (marinho, vinho, bordô, cáqui, verde-oliva, verde-militar, mostarda, caramelo, grafite, off-white, areia, terracota); os valores acima são mapeamentos do XKCD em inglês.
- ISCC-NBS (267 categorias de nomes) e Berlin & Kay (1969, 11 termos básicos): citados de memória, não verificados nesta pesquisa.
- Não há evidência medida de que 1-NN com CIEDE2000 supere limiares HSV neste domínio; comparar no conjunto rotulado.

## 8. Como medir acurácia com 50–100 fotos; tamanho de amostra para afirmar ≥90%

### Takeaway
Reportar acurácia por atributo com intervalo de Wilson de 95% (referência: Brown, Cai e DasGupta 2001), mais top-3, matriz de confusão e cobertura/acurácia seletiva. Com 50–100 fotos não dá para afirmar ≥90% com rigor: em n=100 é preciso acertar 96 para o limite inferior do intervalo passar de 0,90; com 300 fotos bastam ~93,7% observados.

### Cited Findings
- O intervalo de Wilson é assimétrico, não sofre dos defeitos do intervalo de Wald (que colapsa para largura zero perto de 0 ou 1 e pode sair de [0, 1]) e pode ser usado com segurança em amostras pequenas e proporções extremas; Clopper–Pearson nunca fica abaixo da cobertura nominal e por isso costuma ser conservador. — [Wikipedia, Binomial proportion confidence interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)
- Referência padrão: Brown, L. D.; Cai, T. T.; DasGupta, A. (2001), "Interval estimation for a binomial proportion", Statistical Science 16(2): 101–133, doi:10.1214/ss/1009213286. — [Wikipedia](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)
- Cálculo local (Wilson 95% bilateral), acertos/n → intervalo: 45/50 → [0,786; 0,957]; 48/50 → [0,865; 0,989]; 90/100 → [0,826; 0,945]; 95/100 → [0,888; 0,978]; 96/100 → [0,902; 0,984]; 180/200 → [0,851; 0,934]; 190/200 → [0,910; 0,973]; 270/300 → [0,861; 0,929]. — Cálculo desta pesquisa com a fórmula de Wilson descrita em [Wikipedia](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)
- Cálculo local, mínimo de acertos para o limite inferior de Wilson 95% ficar ≥0,90: n=50 → 50/50 (100%); n=75 → 73 (97,3%); n=100 → 96 (96%); n=150 → 143 (95,3%); n=200 → 189 (94,5%); n=300 → 281 (93,7%); n=500 → 464 (92,8%). Para ≥0,85 (cor): n=50 → 48 (96%); n=100 → 92 (92%); n=200 → 180 (90%); n=300 → 268 (89,3%); n=500 → 441 (88,2%). — Cálculo desta pesquisa; método em [Wikipedia](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)
- Precedentes de métrica: o paper do FashionCLIP avalia zero-shot por F1 macro ponderado; a Stitch Fix avaliou cor com ~1.000 imagens anotadas à mão, CIEDE2000 na cor principal e ~200 comparações pareadas manuais. — [Chia et al. 2022](https://www.nature.com/articles/s41598-022-23052-9); [Stitch Fix](https://multithreaded.stitchfix.com/blog/2020/10/13/what-color-is-this-part-2/)

### Inferences
- Relatório mínimo por execução: (a) acurácia top-1 de categoria, de manga, de padrão e de cor (família e tom), cada uma com IC de Wilson 95%; (b) top-3 de categoria (relevante se a interface deixa o usuário confirmar entre 3 sugestões); (c) acurácia por família (5 grupos) e matriz de confusão 30x30 com os pares mais trocados; (d) cobertura (fração não marcada como baixa confiança) e acurácia nos aceitos; (e) latência p50/p95 a quente e a frio.
- Precisão/recall por classe com 30 classes e 100 fotos (~3 por classe) não significam nada: com n=3, 3/3 dá Wilson [0,44; 1,0]. Ou reportar macro-F1 agregado + confusões por família, ou coletar ≥10–20 fotos por classe (300–600 no total).
- Com 50–100 fotos, a afirmação honesta é do tipo "92/100 corretas, IC 95% [0,85; 0,96]"; isso é compatível com ≥90% mas não o demonstra. Para demonstrar ≥90% com acurácia real em torno de 94–95%, planejar ~200–300 fotos de teste; se a acurácia real for ~92%, só ~500+.
- Separar desenvolvimento e teste: prompts, limiares e paleta ajustados no mesmo conjunto inflacionam o resultado. Sugestão: 100 fotos de dev (ajuste) + 200–300 de teste intocado, estratificadas por categoria, cor, fundo e iluminação; fotos de pelo menos 3 celulares/ambientes.
- Comparar variantes (fundo preto vs. branco, FashionCLIP vs. Marqo) nas MESMAS fotos e usar teste pareado (McNemar) sobre discordâncias; diferença de 3–4 pontos em 100 fotos raramente é significativa.
- Definir regras de anotação antes de medir: categorias ambíguas (sweatshirt vs. sweater, chinos vs. dress trousers), cor de peças multicoloridas (cor-base), e aceitar sinônimos de tom (vinho/bordô) no nível família.

### Gaps
- A recomendação exata de Brown, Cai e DasGupta (Wilson ou Jeffreys para n pequeno) não aparece textualmente na página consultada; o artigo original não foi aberto.
- McNemar e bootstrap para comparação pareada: citados de memória, não verificados nesta pesquisa.
- Não há conjunto público de referência com fotos de celular de peça única no esquema de 30 categorias do projeto; o conjunto rotulado terá de ser próprio.
