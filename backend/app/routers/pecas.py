"""Rotas de catalogação e do guarda-roupa digital (seções 6.2 e 6.3)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, UploadFile, status

from ..erros import ErroAPI
from ..repositorio import Repositorio, com_consentimento
from ..schemas import AnaliseFoto, PecaAtualizacao, PecaEntrada
from ..services import visao
from ..services.cor import HEX_REFERENCIA, NEUTRAS, NOMES_CONHECIDOS, hex_para_hsv, nomear
from ..services.taxonomia import CATEGORIAS, POR_CHAVE, papel_coerente

log = logging.getLogger(__name__)

router = APIRouter(prefix="/pecas", tags=["peças"])

TAMANHO_MAXIMO = 12 * 1024 * 1024      # 12 MB: foto de celular cabe com folga
TIPOS_ACEITOS = ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif")


def com_rotulo(linha: dict) -> dict:
    """Acrescenta o nome de exibição da categoria.

    O rótulo não é coluna do banco: ele vive na taxonomia e muda com ela. Guardar
    uma cópia em cada linha criaria peças exibindo nomes antigos depois de uma
    revisão da taxonomia.
    """
    categoria = POR_CHAVE.get(linha.get("categoria", ""))
    publico = {k: v for k, v in linha.items() if not k.startswith("_")}
    return {**publico, "rotulo": categoria.rotulo if categoria else linha.get("categoria")}


@router.get("/taxonomia")
def taxonomia():
    """Catálogo de categorias conhecidas. A interface usa para o seletor manual."""
    return [
        {
            "chave": c.chave, "rotulo": c.rotulo, "papel": c.papel,
            "formalidade": c.formalidade, "temp_min": c.temp_min,
            "temp_max": c.temp_max, "resiste_chuva": c.resiste_chuva,
        }
        for c in CATEGORIAS
    ]


@router.get("/cores")
def cores():
    """Nomes de cor que o sistema reconhece, com a cor de referência de cada um.

    A tela de correção oferece esta lista: escolher pelo nome mantém nome, hex e
    HSV coerentes entre si, e o nome escrito atende a quem não distingue a amostra.
    """
    return [{"nome": n, "hex": HEX_REFERENCIA[n], "neutra": n in NEUTRAS}
            for n in NOMES_CONHECIDOS]


@router.post("/analisar", response_model=AnaliseFoto)
def analisar(
    foto: UploadFile = File(...),
    recorte: bool = True,
    repo: Repositorio = Depends(com_consentimento),
):
    """6.2.1 — análise automática da fotografia.

    Não grava nada: devolve a sugestão para o usuário confirmar ou corrigir.

    É `def`, não `async def`, de propósito: a análise ocupa a CPU por segundos, e
    o FastAPI executa rotas síncronas no threadpool. Como `async def`, ela
    travava o laço de eventos e a API inteira parava — até o /saude.
    """
    if foto.content_type and foto.content_type not in TIPOS_ACEITOS:
        raise ErroAPI(415, "tipo_nao_suportado",
                      "Envie uma imagem JPEG, PNG ou WebP.")
    dados = foto.file.read(TAMANHO_MAXIMO + 1)
    if len(dados) > TAMANHO_MAXIMO:
        raise ErroAPI(413, "foto_grande_demais", "Foto maior que 12 MB.")
    if not dados:
        raise ErroAPI(422, "foto_invalida", "O arquivo enviado está vazio.")
    try:
        return visao.analisar(dados, com_recorte=recorte)
    except visao.FotoInvalida as exc:
        raise ErroAPI(422, "foto_invalida", str(exc))
    except visao.VisaoIndisponivel as exc:
        log.warning("Análise indisponível: %s", exc)
        raise ErroAPI(503, "visao_indisponivel",
                      "A análise automática não está disponível neste servidor. "
                      "Cadastre a peça preenchendo os dados à mão.")


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar(entrada: PecaEntrada, repo: Repositorio = Depends(com_consentimento)):
    """6.2.2 — registro da peça com identificador único."""
    linha = entrada.model_dump()
    caminho = linha.get("imagem_path")
    if caminho and not caminho.startswith(repo.usuario.id + "/"):
        raise ErroAPI(422, "dados_invalidos",
                      "A foto precisa estar na pasta do próprio usuário.")
    return com_rotulo(repo.criar_peca(linha))


@router.get("")
def listar(
    papel: str | None = None,
    categoria: str | None = None,
    cor: str | None = None,
    disponivel: bool | None = None,
    repo: Repositorio = Depends(com_consentimento),
):
    """6.3.1 — consulta e filtro do guarda-roupa."""
    linhas = repo.listar_pecas(papel=papel, categoria=categoria, cor=cor,
                               disponivel=disponivel)
    return [com_rotulo(l) for l in linhas]


def _campos_de_cor(campos: dict) -> None:
    """Mantém nome, hex, HSV e neutralidade coerentes quando a cor é corrigida.

    Antes, corrigir a cor trocava só `cor_nome` e `cor_hex`; o `cor_hsv` antigo
    continuava no banco e seguia alimentando a harmonia de cores e o texto da
    explicação — o chip dizia "verde" e o look era montado como "azul".
    """
    if "cor_hex" not in campos and campos.get("cor_nome") in HEX_REFERENCIA:
        # corrigiu só pelo nome: adota a cor de referência daquele nome
        campos["cor_hex"] = HEX_REFERENCIA[campos["cor_nome"]]
    if "cor_hex" in campos:
        h, s, v = hex_para_hsv(campos["cor_hex"])
        campos["cor_hsv"] = [round(h, 2), round(s, 4), round(v, 4)]
        nome_calculado, neutra = nomear(h, s, v)
        campos.setdefault("cor_nome", nome_calculado)
        campos["neutra"] = neutra or campos["cor_nome"] in NEUTRAS


@router.patch("/{peca_id}")
def atualizar(peca_id: str, mudancas: PecaAtualizacao,
              repo: Repositorio = Depends(com_consentimento)):
    """6.3.1 — edição de atributos e alteração de disponibilidade."""
    campos = {k: v for k, v in mudancas.model_dump().items() if v is not None}
    if not campos:
        raise ErroAPI(400, "nada_para_atualizar", "Nada para atualizar.")

    _campos_de_cor(campos)

    if "categoria" in campos or "papel" in campos:
        atual = repo.obter_peca(peca_id)
        if not atual:
            raise ErroAPI(404, "peca_nao_encontrada", "Peça não encontrada.")
        categoria = campos.get("categoria", atual["categoria"])
        cat = POR_CHAVE.get(categoria)
        if "categoria" in campos and cat:
            # papel, faixa térmica e chuva são propriedades da categoria
            campos.setdefault("papel", cat.papel)
            campos.setdefault("formalidade", cat.formalidade)
            campos.update(temp_min=cat.temp_min, temp_max=cat.temp_max,
                          resiste_chuva=cat.resiste_chuva)
        if not papel_coerente(categoria, campos.get("papel", atual["papel"])):
            raise ErroAPI(422, "dados_invalidos",
                          f"A categoria '{categoria}' não combina com o papel informado.")

    linha = repo.atualizar_peca(peca_id, campos)
    if not linha:
        raise ErroAPI(404, "peca_nao_encontrada", "Peça não encontrada.")
    return com_rotulo(linha)


@router.delete("/{peca_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(peca_id: str, repo: Repositorio = Depends(com_consentimento)):
    """6.3.1 — remoção de uma peça do acervo.

    A foto sai primeiro e a remoção é conferida: o RNF11 fala em remoção
    efetiva, não só do registro. Se o arquivo não puder ser apagado, a peça
    continua no guarda-roupa e o usuário é avisado — melhor repetir a operação
    do que deixar uma foto órfã no bucket sem ninguém saber.
    """
    peca = repo.obter_peca(peca_id)
    if not peca:
        raise ErroAPI(404, "peca_nao_encontrada", "Peça não encontrada.")

    caminho = peca.get("imagem_path")
    if caminho:
        removidas = repo.remover_fotos([caminho])
        if caminho not in removidas:
            # arquivo que já não existe não impede a remoção; falha de permissão, sim
            log.warning("Foto %s não confirmada na remoção da peça %s", caminho, peca_id)
            if repo.foto_existe(caminho):
                raise ErroAPI(502, "foto_nao_removida",
                              "Não foi possível apagar a foto desta peça. Tente de novo.")
    repo.remover_peca(peca_id)
