# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Contract of the Integra Contador API for the DCTFWeb and the MIT.

The service catalogue of the platform is the source of every identifier here.
The MIT services were published on 2025-04-09.
"""

SERPRO_ENVIRONMENT = [
    ("trial", "Trial"),
    ("production", "Production"),
]

SERPRO_BASE_URL = {
    "trial": "https://gateway.apiserpro.serpro.gov.br/integra-contador-trial/v1",
    "production": "https://gateway.apiserpro.serpro.gov.br/integra-contador/v1",
}

SERPRO_TOKEN_URL = {
    "trial": "https://gateway.apiserpro.serpro.gov.br/token",
    "production": "https://gateway.apiserpro.serpro.gov.br/token",
}

# Endpoint by kind of request, as the platform splits them.
ENDPOINT_DECLARE = "Declarar"
ENDPOINT_CONSULT = "Consultar"
ENDPOINT_ISSUE = "Emitir"
ENDPOINT_SUPPORT = "Apoiar"
ENDPOINT_MONITOR = "Monitorar"

SERPRO_ENDPOINT = [
    (ENDPOINT_DECLARE, "Declarar"),
    (ENDPOINT_CONSULT, "Consultar"),
    (ENDPOINT_ISSUE, "Emitir"),
    (ENDPOINT_SUPPORT, "Apoiar"),
    (ENDPOINT_MONITOR, "Monitorar"),
]

SYSTEM_MIT = "MIT"
SYSTEM_DCTFWEB = "DCTFWEB"

SERPRO_SYSTEM = [
    (SYSTEM_MIT, "MIT"),
    (SYSTEM_DCTFWEB, "DCTFWeb"),
]

SERPRO_SYSTEM_VERSION = "1.0"

# Every service this module calls: the identifier, the endpoint it is served
# by, and whether it is billed. Keeping them in one table means a new service
# is one line, and the cost warning cannot forget one.
SERVICES = {
    # MIT
    "close_assessment": {
        "system": SYSTEM_MIT,
        "service": "ENCAPURACAO314",
        "endpoint": ENDPOINT_DECLARE,
        "name": "Close MIT assessment",
        "billed": True,
    },
    "closing_status": {
        "system": SYSTEM_MIT,
        "service": "SITUACAOENC315",
        "endpoint": ENDPOINT_SUPPORT,
        "name": "Consult MIT closing status",
        "billed": False,
    },
    "consult_assessment": {
        "system": SYSTEM_MIT,
        "service": "CONSAPURACAO316",
        "endpoint": ENDPOINT_CONSULT,
        "name": "Consult MIT assessment",
        "billed": True,
    },
    "list_assessments": {
        "system": SYSTEM_MIT,
        "service": "LISTAAPURACOES317",
        "endpoint": ENDPOINT_CONSULT,
        "name": "List MIT assessments by year or month",
        "billed": True,
    },
    # DCTFWeb
    "transmit_declaration": {
        "system": SYSTEM_DCTFWEB,
        "service": "TRANSDECLARACAO310",
        "endpoint": ENDPOINT_DECLARE,
        "name": "Transmit DCTFWeb declaration",
        "billed": True,
    },
    "declaration_receipt": {
        "system": SYSTEM_DCTFWEB,
        "service": "CONSRECIBO32",
        "endpoint": ENDPOINT_CONSULT,
        "name": "Consult the declaration receipt",
        "billed": True,
    },
    "full_declaration": {
        "system": SYSTEM_DCTFWEB,
        "service": "CONSDECCOMPLETA33",
        "endpoint": ENDPOINT_CONSULT,
        "name": "Consult the full declaration",
        "billed": True,
    },
    "declaration_xml": {
        "system": SYSTEM_DCTFWEB,
        "service": "CONSXMLDECLARACAO38",
        "endpoint": ENDPOINT_CONSULT,
        "name": "Consult the declaration XML",
        "billed": True,
    },
    "issue_darf": {
        "system": SYSTEM_DCTFWEB,
        "service": "GERARGUIA31",
        "endpoint": ENDPOINT_ISSUE,
        "name": "Issue the DARF of the declaration",
        "billed": True,
    },
    "issue_darf_in_progress": {
        "system": SYSTEM_DCTFWEB,
        "service": "GERARGUIAANDAMENTO313",
        "endpoint": ENDPOINT_ISSUE,
        "name": "Issue the DARF of a declaration in progress",
        "billed": True,
    },
}

# The category of the DCTFWeb the declaration belongs to. The MIT feeds the
# general monthly one, which is the only category this module builds; the
# others are here because the DARF and the receipt services take them too.
DCTFWEB_CATEGORY_GENERAL = "GERAL_MENSAL"

DCTFWEB_CATEGORY = [
    ("GERAL_MENSAL", "General monthly"),
    ("GERAL_13o_SALARIO", "General 13th salary"),
    ("PF_MENSAL", "Individual monthly"),
    ("PF_13o_SALARIO", "Individual 13th salary"),
    ("AFERICAO", "Works assessment"),
    ("ESPETACULO_DESPORTIVO", "Sporting event"),
    ("RECLAMATORIA_TRABALHISTA", "Labour claim"),
]

# HTTP timeout in seconds. The closing of an assessment is asynchronous on the
# authority side, so the request itself is short.
SERPRO_TIMEOUT = 60

# What the authority answers when the closing is still running.
CLOSING_IN_PROGRESS = "EM_ANDAMENTO"
