"""Testes de ponta a ponta da API.

O motor já é testado isoladamente em `test_recomendador.py`. Aqui o objetivo é
outro: garantir que o *fluxo* funciona por HTTP e que nenhuma situação previsível
produz 500 — a exigência explícita da tarefa. Cada teste percorre o caminho que
o frontend percorre.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.services.recomendador import PESOS_PADRAO


# --------------------------------------------------------------- infraestrutura
def test_saude_anuncia_o_modo(cliente):
    corpo = cliente.get("/saude").json()
    assert corpo["status"] == "ok"
    assert corpo["modo_demo"] is True
    assert corpo["supabase_configurado"] is False


def test_documentacao_interativa_responde(cliente):
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").status_code == 200


def test_tempo_de_resposta_vai_no_cabecalho(cliente):
    """Instrumentação dos RNF01 e RNF02: sem isto a meta é opinião."""
    resposta = cliente.get("/saude")
    assert "X-Tempo-ms" in resposta.headers
    assert float(resposta.headers["X-Tempo-ms"]) >= 0


# --------------------------------------------------------------- catálogos
def test_taxonomia_usa_a_chave_como_identificador(cliente):
    """O frontend seleciona pela `chave`; trocar isso quebra a tela de cadastro."""
    categorias = cliente.get("/pecas/taxonomia").json()
    assert len(categorias) == 24
    assert all({"chave", "rotulo", "papel", "formalidade"} <= set(c) for c in categorias)
    assert {c["papel"] for c in categorias} == {
        "superior", "inferior", "calcado", "sobreposicao"}


def test_eventos_cobrem_as_cinco_formalidades(cliente):
    eventos = cliente.get("/eventos").json()
    assert {e["formalidade"] for e in eventos} == {1, 2, 3, 4, 5}


# --------------------------------------------------------------- guarda-roupa
def test_guarda_roupa_de_exemplo_vem_carregado(cliente):
    """A demonstração precisa mostrar a funcionalidade, não uma tela vazia."""
    pecas = cliente.get("/pecas").json()
    assert len(pecas) >= 12
    assert all(p["rotulo"] for p in pecas)
    assert all(p["codigo"].startswith("CLO-") for p in pecas)


def test_resumo_confirma_que_da_para_recomendar(cliente):
    resumo = cliente.get("/pecas/resumo").json()
    assert resumo["pode_recomendar"] is True
    assert resumo["faltando"] == []
    assert resumo["por_papel"]["calcado"] > 0


def test_filtro_por_papel(cliente):
    calcados = cliente.get("/pecas?papel=calcado").json()
    assert calcados
    assert all(p["papel"] == "calcado" for p in calcados)


def test_cadastro_de_peca_gera_codigo_e_rotulo(cliente):
    nova = {
        "categoria": "mocassim", "papel": "calcado", "formalidade": 4,
        "cor_nome": "marrom", "cor_hex": "#5a3a22", "cor_hsv": [25, 0.62, 0.35],
        "neutra": True, "temp_min": 0, "temp_max": 40, "resiste_chuva": True,
    }
    resposta = cliente.post("/pecas", json=nova)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["rotulo"] == "Mocassim"
    assert corpo["codigo"].startswith("CLO-")
    assert corpo["disponivel"] is True


def test_categoria_invalida_e_recusada_com_422(cliente):
    nova = {
        "categoria": "quimono-espacial", "papel": "superior", "formalidade": 3,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
    }
    resposta = cliente.post("/pecas", json=nova)
    assert resposta.status_code == 422
    assert "quimono-espacial" in resposta.json()["detail"]


def test_formalidade_fora_da_escala_e_recusada(cliente):
    nova = {
        "categoria": "camiseta", "papel": "superior", "formalidade": 9,
        "cor_nome": "azul", "cor_hex": "#2f5f9e", "cor_hsv": [213, 0.7, 0.62],
    }
    assert cliente.post("/pecas", json=nova).status_code == 422


def test_alterar_disponibilidade(cliente):
    peca = cliente.get("/pecas?papel=calcado").json()[0]
    resposta = cliente.patch(f"/pecas/{peca['id']}", json={"disponivel": False})
    assert resposta.status_code == 200
    assert resposta.json()["disponivel"] is False
    assert all(p["id"] != peca["id"] for p in cliente.get("/pecas?disponivel=true").json())


def test_patch_sem_campos_e_400_nao_500(cliente):
    peca = cliente.get("/pecas").json()[0]
    assert cliente.patch(f"/pecas/{peca['id']}", json={}).status_code == 400


def test_peca_inexistente_da_404(cliente):
    inexistente = "00000000-0000-4000-8000-0000000000ff"
    assert cliente.patch(f"/pecas/{inexistente}",
                         json={"disponivel": False}).status_code == 404
    assert cliente.delete(f"/pecas/{inexistente}").status_code == 404


def test_remocao_de_peca(cliente):
    peca = cliente.get("/pecas").json()[0]
    assert cliente.delete(f"/pecas/{peca['id']}").status_code == 204
    assert all(p["id"] != peca["id"] for p in cliente.get("/pecas").json())


# ------------------------------------------------------ fluxo de recomendação
def test_fluxo_completo_de_recomendacao(cliente):
    """O caminho que a tela Recomendar percorre, do pedido ao feedback."""
    resposta = cliente.post("/recomendacoes",
                            json={"evento": "trabalho", "temperatura": 24})
    assert resposta.status_code == 200
    corpo = resposta.json()

    assert corpo["contexto"]["evento"] == "trabalho"
    assert corpo["contexto"]["rotulo_evento"] == "Trabalho"
    assert corpo["contexto"]["formalidade_alvo"] == 3
    assert corpo["contexto"]["clima_automatico"] is False

    assert len(corpo["looks"]) == 3
    for posicao, look in enumerate(corpo["looks"], start=1):
        assert look["posicao"] == posicao
        assert 0 <= look["score"] <= 1
        papeis = {p["papel"] for p in look["pecas"]}
        assert {"superior", "inferior", "calcado"} <= papeis
        assert look["explicacao"].endswith(".")
        # RNF05: a cor precisa estar em texto, não só na amostra visual
        assert all(p["cor_nome"] for p in look["pecas"])

    # os scores vêm em ordem decrescente
    scores = [l["score"] for l in corpo["looks"]]
    assert scores == sorted(scores, reverse=True)


def test_looks_apresentados_sao_distintos(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 26}).json()
    assinaturas = {tuple(sorted(p["id"] for p in l["pecas"])) for l in corpo["looks"]}
    assert len(assinaturas) == 3


def test_frio_inclui_sobreposicao(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 10}).json()
    assert corpo["looks"]
    assert all(any(p["papel"] == "sobreposicao" for p in l["pecas"])
               for l in corpo["looks"])


def test_calor_nao_inclui_sobreposicao(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 33}).json()
    assert all(all(p["papel"] != "sobreposicao" for p in l["pecas"])
               for l in corpo["looks"])


def test_chuva_descarta_calcado_aberto(cliente):
    corpo = cliente.post("/recomendacoes", json={
        "evento": "casual", "temperatura": 28, "chuva_prob": 0.9}).json()
    categorias = {p["categoria"] for l in corpo["looks"] for p in l["pecas"]}
    assert "chinelo" not in categorias
    assert "sandalia" not in categorias


def test_evento_formal_puxa_pecas_sociais(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "formal", "temperatura": 22}).json()
    categorias = {p["categoria"] for l in corpo["looks"] for p in l["pecas"]}
    assert "camisa-social" in categorias
    assert "camiseta" not in categorias


def test_explicacao_cita_temperatura_e_compromisso(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "reuniao", "temperatura": 14}).json()
    texto = corpo["looks"][0]["explicacao"]
    assert "14 °C" in texto
    assert "reunião" in texto.lower()


def test_sem_clima_ainda_recomenda(cliente):
    """RNF07: a ausência de dados de clima não interrompe o uso."""
    resposta = cliente.post("/recomendacoes", json={"evento": "faculdade"})
    assert resposta.status_code == 200
    assert len(resposta.json()["looks"]) == 3
    assert resposta.json()["contexto"]["temperatura"] is None


def test_evento_desconhecido_da_422_com_lista(cliente):
    resposta = cliente.post("/recomendacoes", json={"evento": "baile-de-gala"})
    assert resposta.status_code == 422
    assert "trabalho" in resposta.json()["detail"]


def test_temperatura_absurda_e_recusada_na_validacao(cliente):
    resposta = cliente.post("/recomendacoes",
                            json={"evento": "casual", "temperatura": 500})
    assert resposta.status_code == 422


def test_guarda_roupa_vazio_da_409_explicativo(cliente):
    for peca in cliente.get("/pecas").json():
        cliente.delete(f"/pecas/{peca['id']}")

    resposta = cliente.post("/recomendacoes", json={"evento": "casual"})
    assert resposta.status_code == 409
    assert "vazio" in resposta.json()["detail"].lower()


def test_sem_combinacao_viavel_explica_o_motivo(cliente):
    """Acervo com peças, mas nenhuma serve: a mensagem precisa dizer por quê."""
    for peca in cliente.get("/pecas?papel=calcado").json():
        cliente.delete(f"/pecas/{peca['id']}")

    resposta = cliente.post("/recomendacoes",
                            json={"evento": "casual", "temperatura": 25})
    assert resposta.status_code == 409
    detalhe = resposta.json()["detail"]
    assert "calçado" in detalhe
    assert "25 °C" in detalhe


def test_peca_indisponivel_nao_entra_no_look(cliente):
    calcados = cliente.get("/pecas?papel=calcado").json()
    banido = calcados[0]["id"]
    for c in calcados[1:]:
        cliente.patch(f"/pecas/{c['id']}", json={"disponivel": False})

    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 25}).json()
    usados = {p["id"] for l in corpo["looks"] for p in l["pecas"] if p["papel"] == "calcado"}
    assert usados == {banido}


# --------------------------------------------------------------- feedback
def test_feedback_ajusta_os_pesos(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "trabalho", "temperatura": 24}).json()
    look = corpo["looks"][0]

    resposta = cliente.post("/feedback", json={"look_id": look["id"], "aprovado": True})
    assert resposta.status_code == 200
    pesos = resposta.json()["pesos"]

    assert set(pesos) == set(PESOS_PADRAO)
    assert abs(sum(pesos.values()) - 1.0) < 0.01
    assert pesos != PESOS_PADRAO          # algo de fato mudou


def test_feedback_repetido_no_mesmo_look_nao_duplica(cliente):
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 25}).json()
    look_id = corpo["looks"][0]["id"]
    cliente.post("/feedback", json={"look_id": look_id, "aprovado": True})
    cliente.post("/feedback", json={"look_id": look_id, "aprovado": False})

    metricas = cliente.get("/metricas").json()
    assert metricas["looks_aprovados"] == 0      # a última resposta prevalece


def test_feedback_em_look_inexistente_da_404(cliente):
    resposta = cliente.post("/feedback", json={
        "look_id": "00000000-0000-4000-8000-0000000000ff", "aprovado": True})
    assert resposta.status_code == 404


def test_metricas_calculam_hit_rate_e_precision(cliente):
    """RNF04: Hit Rate@3 conta consultas; Precision@3 conta looks. São distintos."""
    corpo = cliente.post("/recomendacoes",
                         json={"evento": "trabalho", "temperatura": 24}).json()
    cliente.post("/feedback", json={"look_id": corpo["looks"][0]["id"], "aprovado": True})
    cliente.post("/feedback", json={"look_id": corpo["looks"][1]["id"], "aprovado": False})

    metricas = cliente.get("/metricas").json()
    assert metricas["consultas"] == 1
    assert metricas["hit_rate_3"] == 1.0          # 1 de 1 consulta teve aprovação
    assert metricas["precision_3"] == 0.5         # 1 de 2 looks avaliados


def test_metricas_vazias_nao_dividem_por_zero(cliente):
    metricas = cliente.get("/metricas").json()
    assert metricas["consultas"] == 0
    assert metricas["hit_rate_3"] is None
    assert metricas["precision_3"] is None


# --------------------------------------------------------------- análise de foto
def _foto(cor=(210, 40, 40), tamanho=(400, 600), fundo=(250, 250, 250)) -> bytes:
    """Foto sintética: peça colorida centralizada sobre fundo claro."""
    img = Image.new("RGB", tamanho, fundo)
    margem_x, margem_y = tamanho[0] // 5, tamanho[1] // 5
    for x in range(margem_x, tamanho[0] - margem_x):
        for y in range(margem_y, tamanho[1] - margem_y):
            # leve ruído para a imagem não ser considerada borrada
            desvio = 6 if (x + y) % 2 else 0
            img.putpixel((x, y), tuple(min(255, c + desvio) for c in cor))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_analise_mede_a_cor_mesmo_sem_o_modelo(cliente):
    """Sem torch instalado, a cor ainda é real — só a categoria é palpite."""
    resposta = cliente.post("/pecas/analisar",
                            files={"foto": ("peca.png", _foto(), "image/png")})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["cor_nome"] == "vermelho"
    assert corpo["categoria"]
    assert corpo["papel"] in ("superior", "inferior", "calcado", "sobreposicao")
    if not corpo["modelo_disponivel"]:
        assert corpo["aviso"] and "palpite" in corpo["aviso"]


def test_analise_recusa_arquivo_que_nao_e_imagem(cliente):
    resposta = cliente.post("/pecas/analisar",
                            files={"foto": ("nota.txt", b"nao sou imagem", "text/plain")})
    assert resposta.status_code == 415


def test_analise_recusa_arquivo_vazio(cliente):
    resposta = cliente.post("/pecas/analisar",
                            files={"foto": ("vazio.png", b"", "image/png")})
    assert resposta.status_code == 400


def test_analise_recusa_imagem_corrompida(cliente):
    resposta = cliente.post(
        "/pecas/analisar",
        files={"foto": ("quebrada.png", b"\x89PNG\r\n\x1a\nlixo", "image/png")})
    assert resposta.status_code == 422


def test_analise_recusa_foto_pequena(cliente):
    resposta = cliente.post("/pecas/analisar", files={
        "foto": ("mini.png", _foto(tamanho=(64, 64)), "image/png")})
    assert resposta.status_code == 422
    assert "pequena" in resposta.json()["detail"]


@pytest.mark.parametrize("evento", ["casa", "casual", "academia", "faculdade",
                                    "trabalho", "reuniao", "jantar", "formal"])
def test_nenhum_evento_produz_erro_de_servidor(cliente, evento):
    """Varredura: qualquer evento do catálogo responde 200 ou 409, nunca 500."""
    resposta = cliente.post("/recomendacoes",
                            json={"evento": evento, "temperatura": 22})
    assert resposta.status_code in (200, 409), resposta.text


@pytest.mark.parametrize("temperatura", [-5, 0, 8, 15, 18, 22, 28, 35, 42])
def test_nenhuma_temperatura_produz_erro_de_servidor(cliente, temperatura):
    resposta = cliente.post("/recomendacoes",
                            json={"evento": "casual", "temperatura": temperatura})
    assert resposta.status_code in (200, 409), resposta.text


def test_explicacao_respeita_a_cor_corrigida_pelo_usuario(cliente):
    """Se a pessoa corrige o nome da cor, o texto do look tem de usar o dela.

    A explicação recalculava a cor a partir do HSV e ignorava a correção manual,
    então o cartão dizia "azul-marinho" e a frase dizia "azul".
    """
    for peca in cliente.get("/pecas?papel=superior").json():
        cliente.patch(f"/pecas/{peca['id']}", json={"cor_nome": "azul-marinho"})

    corpo = cliente.post("/recomendacoes",
                         json={"evento": "casual", "temperatura": 25}).json()
    assert corpo["looks"]

    look = corpo["looks"][0]
    superior = next(p for p in look["pecas"] if p["papel"] == "superior")
    assert superior["cor_nome"] == "azul-marinho"
    assert "azul-marinho" in look["explicacao"]
