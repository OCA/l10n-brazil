# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

NFSE_NACIONAL_ENVIRONMENTS = [
    ("1", "Produção"),
    ("2", "Produção Restrita"),
]

ADN_BASE_URL = {
    "1": "https://sefin.nfse.gov.br/SefinNacional",
    "2": "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
}

NFSE_NACIONAL_CANCEL_EVENT = "101101"
NFSE_NACIONAL_CANCEL_MOTIVES = [
    ("1", "Erro na emissão"),
    ("2", "Serviço não prestado"),
    ("9", "Outros"),
]
