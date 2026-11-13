"""Rotas de catalogação e do guarda-roupa digital (seções 6.2 e 6.3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..auth import Usuario, usuario_atual
from ..db import como_usuario, proximo_codigo
from ..schemas import AnaliseFoto, PecaAtualizacao, PecaEntrada
from ..services import visao
from ..services.taxonomia import CATEGORIAS, POR_CHAVE

router = APIRouter(prefix="/pecas", tags=["peças"])

TAMANHO_MAXIMO = 12 * 1024 * 1024      # 12 MB: foto de celular cabe com folga


def _com_rotulo(linha: dict) -> dict:
    """Acrescenta o nome de exibição da categoria.

    O rótulo não é coluna do banco: ele vive na taxonomia e muda com ela. Guardar
    uma cópia em cada linha criaria peças exibindo nomes antigos depois de uma
    revisão da taxonomia.
    """
    categoria = POR_CHAVE.get(linha.get("categoria", ""))
    return {**linha, "rotulo": categoria.rotulo if categoria else linha.get("categoria")}


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


@router.post("/analisar", response_model=AnaliseFoto)
async def analisar(
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(usuario_atual),
):
    """6.2.1 — análise automática da fotografia.

    Não grava nada: devolve a sugestão para o usuário confirmar ou corrigir.
    """
    dados = await foto.read()
    if len(dados) > TAMANHO_MAXIMO:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            "Foto maior que 12 MB.")
    try:
        return visao.analisar(dados)
    except visao.FotoInvalida as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar(entrada: PecaEntrada, usuario: Usuario = Depends(usuario_atual)):
    """6.2.2 — registro da peça com identificador único."""
    cliente = como_usuario(usuario)
    codigo = proximo_codigo(cliente, usuario.id)

    linha = entrada.model_dump()
    linha.update(usuario_id=usuario.id, codigo=codigo, revisada=True)

    resposta = cliente.table("pecas").insert(linha).execute()
    return _com_rotulo(resposta.data[0])


@router.get("")
def listar(
    papel: str | None = None,
    categoria: str | None = None,
    cor: str | None = None,
    disponivel: bool | None = None,
    usuario: Usuario = Depends(usuario_atual),
):
    """6.3.1 — consulta e filtro do guarda-roupa."""
    consulta = como_usuario(usuario).table("pecas").select("*")
    if papel:
        consulta = consulta.eq("papel", papel)
    if categoria:
        consulta = consulta.eq("categoria", categoria)
    if cor:
        consulta = consulta.eq("cor_nome", cor)
    if disponivel is not None:
        consulta = consulta.eq("disponivel", disponivel)
    linhas = consulta.order("criado_em", desc=True).execute().data
    return [_com_rotulo(l) for l in linhas]


@router.patch("/{peca_id}")
def atualizar(peca_id: str, mudancas: PecaAtualizacao,
              usuario: Usuario = Depends(usuario_atual)):
    """6.3.1 — edição de atributos e alteração de disponibilidade."""
    campos = {k: v for k, v in mudancas.model_dump().items() if v is not None}
    if not campos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nada para atualizar.")

    resposta = (como_usuario(usuario).table("pecas")
                .update(campos).eq("id", peca_id).execute())
    if not resposta.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Peça não encontrada.")
    return _com_rotulo(resposta.data[0])


@router.delete("/{peca_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(peca_id: str, usuario: Usuario = Depends(usuario_atual)):
    """6.3.1 — remoção de uma peça do acervo."""
    cliente = como_usuario(usuario)
    peca = cliente.table("pecas").select("imagem_path").eq("id", peca_id).execute()
    if not peca.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Peça não encontrada.")

    caminho = peca.data[0].get("imagem_path")
    cliente.table("pecas").delete().eq("id", peca_id).execute()
    if caminho:
        # a imagem some junto: o RNF11 fala em remoção efetiva, não só do registro
        try:
            cliente.storage.from_("pecas").remove([caminho])
        except Exception:                        # noqa: BLE001
            pass
