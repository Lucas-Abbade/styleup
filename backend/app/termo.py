"""Termo de consentimento exibido antes do primeiro uso.

RASCUNHO TÉCNICO — precisa de revisão do orientador e, se houver, do encarregado
de dados da instituição antes do teste com usuários reais. O conteúdo segue o
que a LGPD (Lei 13.709/2018) pede no art. 9º: finalidade, forma e duração do
tratamento, identificação e contato do controlador, compartilhamento e direitos
do titular. Preencha CONTROLADOR e CONTATO antes de publicar.

Mudou o texto ou alguma finalidade? Mude VERSAO_TERMO (config): todos os
usuários voltam a ser consultados (art. 8º, § 6º).
"""

from __future__ import annotations

from .config import config

CONTROLADOR = "Equipe do projeto StyleUp (projeto acadêmico)"
CONTATO = "PREENCHER: e-mail de contato da equipe"


def termo() -> dict:
    return {
        "versao": config.versao_termo,
        "titulo": "Como o Style Up usa os seus dados",
        "resumo": ("O Style Up guarda as fotos das suas roupas e o que você achou dos "
                   "looks para montar combinações melhores. Você pode apagar tudo "
                   "quando quiser."),
        "controlador": CONTROLADOR,
        "contato": CONTATO,
        "secoes": [
            {"titulo": "O que coletamos",
             "itens": [
                 "Nome e e-mail, para criar e proteger a sua conta.",
                 "As fotos das peças que você cadastrar. Guardamos só o recorte da "
                 "peça, sem o fundo da foto.",
                 "Categoria, cor e demais características de cada peça.",
                 "Os looks gerados, o que você aprovou, rejeitou ou salvou, e as "
                 "preferências aprendidas a partir disso.",
             ]},
            {"titulo": "Para que usamos",
             "itens": [
                 "Montar o seu guarda-roupa digital e sugerir looks.",
                 "Ajustar as sugestões ao seu gosto.",
                 "Medir, de forma agregada, se as sugestões estão acertando "
                 "(avaliação acadêmica do projeto).",
             ]},
            {"titulo": "Localização (opcional)",
             "itens": [
                 "Se você permitir, usamos a sua posição aproximada (cerca de 1 km) "
                 "apenas para consultar a previsão do tempo no momento do pedido.",
                 "A posição não é gravada. Sem essa permissão o app funciona "
                 "normalmente: basta informar a temperatura.",
             ]},
            {"titulo": "Com quem compartilhamos",
             "itens": [
                 "Supabase (banco de dados, login e armazenamento das fotos), que "
                 "pode manter servidores fora do Brasil.",
                 "Open-Meteo (previsão do tempo), que recebe apenas a posição "
                 "aproximada, sem nenhum dado que identifique você.",
                 "Não vendemos nem cedemos seus dados a terceiros.",
             ]},
            {"titulo": "Por quanto tempo",
             "itens": [
                 "Enquanto a sua conta existir. Ao excluir a conta, fotos e "
                 "registros são apagados de forma definitiva.",
             ]},
            {"titulo": "Seus direitos",
             "itens": [
                 "Ver, corrigir e baixar os seus dados (Perfil › Meus dados).",
                 "Retirar este consentimento ou excluir a conta a qualquer momento "
                 "(Perfil › Privacidade), sem custo.",
                 f"Falar com a equipe: {CONTATO}.",
             ]},
            {"titulo": "Idade",
             "itens": ["O Style Up é destinado a maiores de 18 anos."]},
        ],
        "finalidades": [
            {"chave": "essencial", "obrigatoria": True,
             "rotulo": "Guardar minhas peças, looks e avaliações para gerar sugestões."},
            {"chave": "localizacao", "obrigatoria": False,
             "rotulo": "Usar minha localização aproximada para consultar o clima."},
        ],
    }
