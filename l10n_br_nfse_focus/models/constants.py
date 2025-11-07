# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Constants for FocusNFE NFSe integration."""

NFSE_URL = {
    "1": "https://api.focusnfe.com.br",
    "2": "https://homologacao.focusnfe.com.br",
}

API_ENDPOINT = {
    "envio": "/v2/nfse?",
    "status": "/v2/nfse/",
    "resposta": "/v2/nfse/",
    "cancelamento": "/v2/nfse/",
}

API_ENDPOINT_NACIONAL = {
    "envio": "/v2/nfsen",
    "status": "/v2/nfsen/",
    "resposta": "/v2/nfsen/",
    "cancelamento": "/v2/nfsen/",
}

TIMEOUT = 60  # 60 seconds

# Constants for document status
STATUS_AUTORIZADO = "autorizado"
STATUS_CANCELADO = "cancelado"
STATUS_ERRO_AUTORIZACAO = "erro_autorizacao"
STATUS_PROCESSANDO_AUTORIZACAO = "processando_autorizacao"
CODE_NFE_CANCELADA = "nfe_cancelada"
CODE_NFE_AUTORIZADA = "nfe_autorizada"

# CPF/CNPJ length constants
CPF_LENGTH = 11
CNPJ_LENGTH = 14

# PDF validation constants
PDF_HEADER = b"%PDF-"
PDF_FOOTER = b"%%EOF"
