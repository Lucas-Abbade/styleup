# Conjunto de avaliação da visão (fase 4)

Coloque aqui de 50 a 100 fotos reais, uma peça por foto, e rotule cada uma em
`rotulos.csv`. Depois rode, na pasta `backend/`:

```bash
python -m scripts.medir_acuracia            # gera avaliacao/relatorio.md e .json
python -m scripts.medir_acuracia --valores  # lista os valores aceitos
```

## Formato

```
avaliacao/
  rotulos.csv
  fotos/
    camiseta_preta_01.jpg
    calca_jeans_02.jpg
```

`rotulos.csv` — UTF-8, vírgula como separador, primeira linha é o cabeçalho:

| Coluna | Obrigatória | Valores |
|---|---|---|
| `arquivo` | sim | nome do arquivo em `fotos/` |
| `categoria` | sim | chave da taxonomia (`camiseta`, `polo`, `calca-jeans`, `tenis`, `bone`…) |
| `cor` | sim | nome de cor do sistema (`preto`, `grafite`, `marinho`, `verde-oliva`…) |
| `estilo` | não | `esportivo`, `casual`, `casual-arrumado`, `social`, `formal` |
| `manga` | não | `curta`, `longa` — deixe vazio se não se aplica (calça, tênis) |
| `estampa` | não | `lisa`, `listrada`, `estampada`, `xadrez` |

Exemplo:

```csv
arquivo,categoria,cor,estilo,manga,estampa
camiseta_preta_01.jpg,camiseta,preto,esportivo,curta,lisa
calca_jeans_02.jpg,calca-jeans,azul,casual,,lisa
tenis_branco_03.jpg,tenis-casual,branco,casual-arrumado,,
```

## Como montar um conjunto que valha

- Fotos tiradas como o usuário tira: celular, luz de casa, fundo comum. Foto de
  catálogo infla o resultado.
- Pelo menos 3 fotos por categoria que vocês pretendem defender; com menos, a
  linha "por classe" do relatório não diz nada.
- Rotule a cor **olhando a peça**, não a foto, e use os nomes do sistema.
- Quem rotula não deve ver a resposta do modelo antes.

As fotos não entram no git (`.gitignore`): são dados pessoais dos voluntários.
