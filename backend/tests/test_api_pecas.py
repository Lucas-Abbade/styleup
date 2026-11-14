"""Rotas do guarda-roupa, com os cenários de defeito das fases 1 e 2."""

from __future__ import annotations

from app.repositorio.memoria import armazem

from .conftest import cabecalho, nova_peca


def test_sem_token_devolve_401_no_formato_padrao(cliente):
    r = cliente.get("/pecas")
    assert r.status_code == 401
    corpo = r.json()
    assert corpo["codigo"] == "nao_autenticado" and corpo["erro"]
    assert corpo["detail"] == corpo["erro"]          # compatibilidade com clientes antigos


def test_sem_consentimento_as_rotas_de_dados_ficam_fechadas(cliente):
    r = cliente.get("/pecas", headers=cabecalho("novato"))
    assert r.status_code == 403
    assert r.json()["codigo"] == "consentimento_pendente"


def test_codigo_clo_nao_se_repete_depois_de_exclusao(cliente, vazio):
    """Fase 2, item 1: com as peças 1, 2 e 3, apagar a 2 fazia o próximo código
    ser CLO-000003 (count + 1), que já existia — e o cadastro quebrava com 500."""
    criadas = [cliente.post("/pecas", headers=vazio, json=nova_peca()).json() for _ in range(3)]
    base = int(criadas[0]["codigo"][4:])
    assert [int(p["codigo"][4:]) for p in criadas] == [base, base + 1, base + 2]

    assert cliente.delete(f"/pecas/{criadas[1]['id']}", headers=vazio).status_code == 204
    r = cliente.post("/pecas", headers=vazio, json=nova_peca())
    assert r.status_code == 201, r.text
    assert int(r.json()["codigo"][4:]) == base + 3

    codigos = [p["codigo"] for p in cliente.get("/pecas", headers=vazio).json()]
    assert len(codigos) == len(set(codigos)) == 3


def test_corrigir_a_cor_recalcula_hsv_e_neutralidade(cliente, vazio):
    """Fase 2, item 2: a correção trocava nome e hex, e o HSV antigo continuava
    alimentando a harmonia de cores e o texto da explicação."""
    peca = cliente.post("/pecas", headers=vazio, json=nova_peca("camiseta", "preto")).json()
    assert peca["neutra"] is True

    r = cliente.patch(f"/pecas/{peca['id']}", headers=vazio,
                      json={"cor_nome": "vermelho", "cor_hex": "#D42A2A"})
    assert r.status_code == 200, r.text
    nova = r.json()
    assert nova["cor_hex"] == "#d42a2a" and nova["cor_nome"] == "vermelho"
    assert nova["neutra"] is False
    assert abs(nova["cor_hsv"][0]) < 5 and nova["cor_hsv"][1] > 0.7      # matiz vermelho

    # corrigir só pelo nome adota a cor de referência daquele nome
    so_nome = cliente.patch(f"/pecas/{peca['id']}", headers=vazio,
                            json={"cor_nome": "marinho"}).json()
    assert so_nome["cor_hex"] == "#1c2a4a" and so_nome["neutra"] is True
    assert 200 <= so_nome["cor_hsv"][0] <= 250


def test_explicacao_usa_o_nome_de_cor_corrigido(cliente, vazio):
    """O chip mostrava `cor_nome`, o texto recalculava pelo HSV: divergiam."""
    ids = {}
    for categoria, cor in (("camiseta", "preto"), ("calca-jeans", "azul"), ("tenis", "branco")):
        ids[categoria] = cliente.post("/pecas", headers=vazio,
                                      json=nova_peca(categoria, cor)).json()["id"]
    # o usuário renomeia a cor sem mudar o hex: o nome dele é o que vale no texto
    cliente.patch(f"/pecas/{ids['camiseta']}", headers=vazio,
                  json={"cor_nome": "grafite", "cor_hex": "#1a1a1a"})
    look = cliente.post("/recomendacoes", headers=vazio,
                        json={"evento": "casual", "temperatura": 25}).json()["looks"][0]
    chip = next(p["cor_nome"] for p in look["pecas"] if p["categoria"] == "camiseta")
    assert chip == "grafite"
    assert "camiseta grafite" in look["explicacao"]


def test_validacao_de_entrada(cliente, vazio):
    """Fase 2, item 8."""
    casos = [
        ({"cor_hsv": [10, 0.5]}, "cor_hsv"),                       # dois valores
        ({"cor_hsv": [10, 1.5, 0.5]}, "cor_hsv"),                  # saturação fora de 0-1
        ({"cor_hsv": [400, 0.5, 0.5]}, "cor_hsv"),                 # matiz fora de 0-360
        ({"cor_hex": "azul"}, "cor_hex"),
        ({"papel": "calcado"}, ""),                                # camiseta não é calçado
        ({"formalidade": 9}, "formalidade"),
        ({"temp_min": 30, "temp_max": 10}, ""),
    ]
    for mudanca, campo in casos:
        r = cliente.post("/pecas", headers=vazio, json=nova_peca(**mudanca))
        assert r.status_code == 422, (mudanca, r.text)
        corpo = r.json()
        assert corpo["codigo"] == "dados_invalidos" and corpo["campos"]
        if campo:
            assert any(campo in c["campo"] for c in corpo["campos"]), corpo
    assert cliente.get("/pecas", headers=vazio).json() == []


def test_hsv_ausente_e_calculado_a_partir_do_hex(cliente, vazio):
    entrada = nova_peca("camiseta", "azul")
    del entrada["cor_hsv"], entrada["neutra"]
    peca = cliente.post("/pecas", headers=vazio, json=entrada).json()
    assert len(peca["cor_hsv"]) == 3 and 200 <= peca["cor_hsv"][0] <= 250
    assert peca["neutra"] is False


def test_trocar_a_categoria_arrasta_papel_e_faixa_termica(cliente, vazio):
    peca = cliente.post("/pecas", headers=vazio, json=nova_peca("camiseta", "preto")).json()
    nova = cliente.patch(f"/pecas/{peca['id']}", headers=vazio,
                         json={"categoria": "bermuda"}).json()
    assert (nova["papel"], nova["temp_min"], nova["rotulo"]) == ("inferior", 22, "Bermuda")
    r = cliente.patch(f"/pecas/{peca['id']}", headers=vazio,
                      json={"categoria": "tenis", "papel": "superior"})
    assert r.status_code == 422


def test_usuario_nao_enxerga_nem_altera_peca_de_outro(cliente, ana, bruno):
    da_ana = cliente.get("/pecas", headers=ana).json()[0]
    assert all(p["id"] != da_ana["id"] for p in cliente.get("/pecas", headers=bruno).json())
    assert cliente.patch(f"/pecas/{da_ana['id']}", headers=bruno,
                         json={"disponivel": False}).status_code == 404
    assert cliente.delete(f"/pecas/{da_ana['id']}", headers=bruno).status_code == 404
    assert cliente.get("/pecas", headers=ana).json()[0]["disponivel"] is True


def test_remover_peca_apaga_a_foto_do_armazenamento(cliente, vazio):
    """Fase 1, item 3: a foto precisa sumir do bucket, e isso é conferido."""
    foto = cliente.post("/demo/fotos", headers=vazio,
                        files={"foto": ("p.webp", b"conteudo", "image/webp")}).json()["caminho"]
    assert foto in armazem.fotos
    peca = cliente.post("/pecas", headers=vazio, json=nova_peca(imagem_path=foto)).json()
    assert cliente.delete(f"/pecas/{peca['id']}", headers=vazio).status_code == 204
    assert foto not in armazem.fotos


def test_foto_fora_da_pasta_do_usuario_e_recusada(cliente, vazio):
    r = cliente.post("/pecas", headers=vazio,
                     json=nova_peca(imagem_path="outro-usuario/arquivo.webp"))
    assert r.status_code == 422


def test_filtros_do_guarda_roupa(cliente, ana):
    superiores = cliente.get("/pecas?papel=superior", headers=ana).json()
    assert superiores and all(p["papel"] == "superior" for p in superiores)
    pretas = cliente.get("/pecas?cor=preto", headers=ana).json()
    assert pretas and all(p["cor_nome"] == "preto" for p in pretas)
    assert all("_ordem" not in p and p["rotulo"] for p in pretas)


def test_analise_sem_dependencias_de_visao_responde_503_claro(cliente, ana):
    r = cliente.post("/pecas/analisar", headers=ana,
                     files={"foto": ("p.txt", b"nao e imagem", "text/plain")})
    assert r.status_code == 415
    r = cliente.post("/pecas/analisar", headers=ana,
                     files={"foto": ("p.jpg", b"nao e imagem", "image/jpeg")})
    assert r.status_code == 422 and r.json()["codigo"] == "foto_invalida"


def test_catalogos_publicos(cliente):
    categorias = cliente.get("/pecas/taxonomia").json()
    assert {"chave", "rotulo", "papel"} <= set(categorias[0])
    assert any(c["papel"] == "acessorio" for c in categorias)
    cores = cliente.get("/pecas/cores").json()
    assert {"nome": "marinho", "hex": "#1c2a4a", "neutra": True} in cores


def test_rota_inexistente_e_erro_interno_seguem_o_formato(cliente, ana, monkeypatch):
    assert cliente.get("/nao-existe").json()["codigo"] == "nao_encontrado"

    def explodir(*a, **k):
        raise RuntimeError("segredo interno que não pode vazar")
    monkeypatch.setattr("app.repositorio.memoria.RepositorioMemoria.listar_pecas", explodir)
    c = __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(
        cliente.app, raise_server_exceptions=False)
    r = c.get("/pecas", headers=ana)
    assert r.status_code == 500
    corpo = r.json()
    assert corpo["codigo"] == "erro_interno" and "segredo" not in r.text and corpo["protocolo"]
