# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

SEFIN_URL = {
    "1": "https://sefin.nfse.gov.br/SefinNacional",
    "2": "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
}

ADN_URL = {
    "1": "https://adn.nfse.gov.br",
    "2": "https://adn.producaorestrita.nfse.gov.br",
}

CNC_URL = {
    "1": "https://adn.nfse.gov.br/cnc",
    "2": "https://adn.producaorestrita.nfse.gov.br/cnc",
}

DANFSE_URL = {
    "1": "https://adn.nfse.gov.br/danfse",
    "2": "https://adn.producaorestrita.nfse.gov.br/danfse",
}

PARAMETRIZACAO_URL = {
    "1": "https://adn.nfse.gov.br/parametrizacao",
    "2": "https://adn.producaorestrita.nfse.gov.br/parametrizacao",
}

API_ENDPOINT_NACIONAL = {
    "issue": "/nfse/v1/dps",
    "query": "/nfse/v1/nfse/",
    "cancel": "/nfse/v1/nfse/",
    "substitute": "/nfse/v1/dps",
}

API_ENDPOINT_ADN = {
    "contributor_nfse": "/contribuintes/nfse/",
    "contributor_dps": "/contribuintes/dps/",
    "municipality_nfse": "/municipios/nfse/",
}

API_ENDPOINT_CNC = {
    "query_nfse": "/nfse/",
    "query_municipality": "/municipio/nfse/",
    "query_consolidated": "/consulta/nfse/",
}

API_ENDPOINT_DANFSE = {
    "render": "/danfse/",
}

TIMEOUT = 60

STATUS_AUTORIZADO = "autorizado"
STATUS_CANCELADO = "cancelado"
STATUS_ERRO = "erro"
STATUS_PROCESSANDO = "processando"

CODE_NFE_AUTORIZADA = "nfe_autorizada"
CODE_NFE_CANCELADA = "nfe_cancelada"

PDF_HEADER = b"%PDF-"
PDF_FOOTER = b"%%EOF"

CPF_LENGTH = 11
CNPJ_LENGTH = 14
