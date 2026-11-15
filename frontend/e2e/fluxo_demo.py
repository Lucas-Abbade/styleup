"""Percorre o app inteiro no modo demonstração e salva uma captura de cada tela.

Uso (com a API e o front rodando em modo demonstração):

    pip install playwright            # usa o Chrome instalado na máquina
    python frontend/e2e/fluxo_demo.py [pasta_de_saida]

Falha (código ≠ 0) se alguma etapa não acontecer ou se o console do navegador
registrar erro. Serve de teste de fumaça antes de uma apresentação.
"""

from __future__ import annotations

import json
import os
import struct
import sys
import zlib
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://localhost:5173"
SAIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "capturas")
SAIDA.mkdir(parents=True, exist_ok=True)
AXE = Path(__file__).resolve().parent.parent / "node_modules" / "axe-core" / "axe.min.js"
erros: list[str] = []
acessibilidade: list[str] = []


def png_de_teste(lado: int = 480) -> bytes:
    """PNG com ruído (nítido o bastante para passar na validação de foco)."""
    linhas = b"".join(b"\x00" + os.urandom(lado * 3) for _ in range(lado))

    def bloco(tipo: bytes, dados: bytes) -> bytes:
        return (struct.pack(">I", len(dados)) + tipo + dados
                + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linhas, 1)) + bloco(b"IEND", b""))


def auditar(pagina, tela: str) -> None:
    """Checagem automática de acessibilidade (axe-core, regras WCAG 2.x A e AA)
    e de largura: conteúdo mais largo que a tela faz o celular reduzir o zoom."""
    largura = pagina.evaluate("document.documentElement.scrollWidth")
    if largura > 392:
        acessibilidade.append(f"{tela}: a página ficou com {largura}px de largura (tela: 390px)")
    if not AXE.exists():
        return
    pagina.add_script_tag(path=str(AXE))
    resultado = pagina.evaluate(
        "axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']})")
    for v in resultado["violations"]:
        alvos = "; ".join(" ".join(n["target"]) for n in v["nodes"][:3])
        acessibilidade.append(f"{tela}: [{v['impact']}] {v['id']} — {v['help']} ({alvos})")


def foto(pagina, nome: str, inteira: bool = False) -> None:
    pagina.wait_for_timeout(350)
    pagina.screenshot(path=str(SAIDA / f"{nome}.png"), full_page=inteira)


with sync_playwright() as p:
    navegador = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    contexto = navegador.new_context(viewport={"width": 390, "height": 844},
                                     device_scale_factor=2, locale="pt-BR",
                                     has_touch=True, is_mobile=True)
    pagina = contexto.new_page()
    pagina.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: erros.append(str(e)))

    # 1. splash → criar conta
    pagina.goto(BASE)
    expect(pagina.get_by_role("heading", name="Style Up")).to_be_visible()
    foto(pagina, "01-splash")
    auditar(pagina, "splash")
    pagina.get_by_role("link", name="Começar").click()
    pagina.get_by_label("Como quer ser chamado").fill("Pedro")
    # no modo demonstração não há e-mail nem senha
    if pagina.get_by_label("E-mail").count():
        pagina.get_by_label("E-mail").fill(f"pedro{id(pagina) % 100000}@exemplo.dev")
        pagina.get_by_label("Senha").fill("segredo123")
    foto(pagina, "02-criar-conta")
    auditar(pagina, "criar conta")
    pagina.get_by_role("button", name="Criar conta").click()

    # 2. consentimento (LGPD): o botão só libera depois do aceite
    expect(pagina.get_by_role("heading", name="Como o Style Up usa os seus dados")).to_be_visible()
    aceitar = pagina.get_by_role("button", name="Aceitar e continuar")
    expect(aceitar).to_be_disabled()
    foto(pagina, "03-consentimento", inteira=True)
    auditar(pagina, "consentimento")
    pagina.get_by_role("checkbox").first.check()
    aceitar.click()

    # 3. início
    expect(pagina.get_by_role("heading", name="Olá, Pedro.")).to_be_visible()
    expect(pagina.get_by_role("navigation", name="Navegação principal")).to_be_visible()
    foto(pagina, "04-inicio")
    auditar(pagina, "início")
    foto(pagina, "04-inicio-inteira", inteira=True)

    # 4. guarda-roupa: filtro, edição de cor e disponibilidade
    pagina.get_by_role("link", name="Guarda-Roupa").first.click()
    expect(pagina.get_by_role("heading", name="Meu Guarda-Roupa")).to_be_visible()
    expect(pagina.locator(".cartao-peca")).to_have_count(24)
    foto(pagina, "05-guarda-roupa")
    auditar(pagina, "guarda-roupa")
    foto(pagina, "05-guarda-roupa-inteira", inteira=True)
    pagina.get_by_role("button", name="Calças", exact=True).click()
    expect(pagina.locator(".cartao-peca")).to_have_count(5)
    pagina.get_by_role("button", name="Todas", exact=True).click()
    pagina.get_by_role("button", name="Camiseta, preto. Abrir detalhes").click()
    dialogo = pagina.get_by_role("dialog")
    expect(dialogo).to_be_visible()
    foto(pagina, "06-editar-peca")
    auditar(pagina, "editar peça")
    dialogo.get_by_role("button", name="Vinho", exact=True).click()   # grava na hora
    expect(pagina.get_by_text("Cor atualizada")).to_be_visible()
    dialogo.get_by_role("button", name="Fechar").click()
    expect(pagina.locator(".cartao-peca", has_text="Camiseta").filter(has_text="Vinho")).to_have_count(1)

    # 5. cadastro: sem foto e com foto (o servidor de teste não tem os modelos de
    #    visão; a tela deve cair para o preenchimento manual, sem perder a foto)
    pagina.get_by_role("link", name="Adicionar peça").click()
    foto(pagina, "07-nova-peca")
    auditar(pagina, "nova peça")
    pagina.get_by_role("button", name="Cadastrar sem foto").click()
    pagina.get_by_label("Categoria", exact=True).select_option("jaqueta-couro")
    pagina.get_by_label("Cor", exact=True).select_option("preto")
    foto(pagina, "08-confirmar-peca")
    auditar(pagina, "confirmar peça")
    pagina.get_by_role("button", name="Salvar no guarda-roupa").click()
    expect(pagina.locator(".cartao-peca")).to_have_count(25)

    pagina.get_by_role("link", name="Adicionar peça").click()
    pagina.locator("input[type=file]:not([capture])").set_input_files(
        {"name": "peca.png", "mimeType": "image/png", "buffer": png_de_teste()})
    visao = pagina.request.get("http://localhost:8000/saude").json()["visao"]["situacao"]
    if visao == "pronto":
        expect(pagina.get_by_text("Confira o que identifiquei")).to_be_visible(timeout=60000)
    else:
        expect(pagina.get_by_text("A análise automática não está disponível")).to_be_visible(timeout=20000)
    pagina.get_by_label("Categoria", exact=True).select_option("mochila")
    pagina.get_by_label("Cor", exact=True).select_option("verde-oliva")
    foto(pagina, "08b-confirmar-com-foto")
    pagina.get_by_role("button", name="Salvar no guarda-roupa").click()
    expect(pagina.locator(".cartao-peca")).to_have_count(26)
    com_foto = pagina.locator(".cartao-peca", has_text="Mochila").locator("img")
    expect(com_foto).to_have_attribute("src", __import__("re").compile(r"/demo/fotos/"))
    assert com_foto.evaluate("i => i.complete && i.naturalWidth > 0"), "a foto enviada não carregou"

    # 6. gerador → look
    pagina.get_by_role("link", name="Gerador").first.click()
    expect(pagina.get_by_role("heading", name="Gerador de Looks")).to_be_visible()
    pagina.get_by_label("Qual look você quer criar hoje?").fill("Look para a faculdade, casual")
    pagina.get_by_role("button", name="Dias frios").click()
    foto(pagina, "09-gerador")
    auditar(pagina, "gerador")
    pagina.get_by_role("button", name="Gerar look", exact=True).click()
    expect(pagina.get_by_role("heading", name="Look Gerado")).to_be_visible()
    expect(pagina.locator(".colagem .foto-peca").first).to_be_visible()
    foto(pagina, "10-look")
    auditar(pagina, "look gerado")
    foto(pagina, "10-look-inteira", inteira=True)

    # exportar o look como imagem
    with pagina.expect_download() as baixado:
        pagina.get_by_role("button", name="Baixar imagem do look").click()
    destino = SAIDA / "look-exportado.png"
    baixado.value.save_as(str(destino))
    assert destino.stat().st_size > 20_000, "a imagem exportada do look veio vazia"

    # 7. reagir, salvar, trocar de opção
    pagina.get_by_role("button", name="Gostei", exact=True).click()
    expect(pagina.get_by_role("button", name="Gostei", exact=True)).to_have_attribute("aria-pressed", "true")
    pagina.get_by_role("button", name="Salvar no Guarda-Roupa").click()
    expect(pagina.get_by_role("button", name="Salvo no Guarda-Roupa")).to_be_visible()
    primeiro = pagina.locator(".tira-pecas").inner_text()
    pagina.get_by_role("button", name="Gerar outro look").click()
    expect(pagina.get_by_role("tab", name="Opção 2 de 3")).to_have_attribute("aria-selected", "true")
    assert pagina.locator(".tira-pecas").inner_text() != primeiro, "o segundo look é igual ao primeiro"
    pagina.locator("summary", has_text="Por que este look?").click()
    foto(pagina, "11-look-explicado", inteira=True)

    # 8. looks salvos no guarda-roupa
    pagina.get_by_role("link", name="Guarda-Roupa").first.click()
    pagina.get_by_role("button", name="Looks salvos").click()
    expect(pagina.locator(".look-mini")).to_have_count(1)
    foto(pagina, "12-looks-salvos")

    # 9. comunidade e perfil
    pagina.get_by_role("link", name="Comunidade").first.click()
    expect(pagina.get_by_role("heading", name="Em breve")).to_be_visible()
    foto(pagina, "13-comunidade")
    pagina.get_by_role("link", name="Perfil").first.click()
    expect(pagina.get_by_text("100%").first).to_be_visible()      # 1 consulta, 1 acerto
    foto(pagina, "14-perfil", inteira=True)
    auditar(pagina, "perfil")

    # 10. excluir conta volta à tela inicial
    pagina.get_by_role("button", name="Excluir minha conta").click()
    excluir = pagina.get_by_role("button", name="Excluir tudo")
    expect(excluir).to_be_disabled()
    pagina.get_by_label("Digite EXCLUIR para confirmar").fill("excluir")
    foto(pagina, "15-excluir-conta")
    excluir.click()
    expect(pagina.get_by_role("link", name="Começar")).to_be_visible()

    navegador.close()

# sem os modelos de visão no servidor, o 503 de /pecas/analisar é o esperado
if visao != "pronto":
    erros = [e for e in erros if "503" not in e]
if erros:
    print("ERROS NO CONSOLE DO NAVEGADOR:")
    for e in erros:
        print("  -", e[:300])
    sys.exit(1)
if acessibilidade:
    print("PROBLEMAS DE ACESSIBILIDADE (axe-core):")
    for a in acessibilidade:
        print("  -", a)
    sys.exit(1)
print(f"OK: fluxo completo, sem erro no console e sem violação de acessibilidade; "
      f"capturas em {SAIDA}/")
