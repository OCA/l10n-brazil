# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import TP_ATIV  # noqa: F401

EVENT_D1001 = "D-1001"
EVENT_D1011 = "D-1011"
EVENT_D1101 = "D-1101"
EVENT_D1106 = "D-1106"
EVENT_D1121 = "D-1121"
EVENT_D1198 = "D-1198"
EVENT_D1199 = "D-1199"

EVENT_TYPES = [
    (EVENT_D1001, "D-1001 Taxpayer information"),
    (EVENT_D1011, "D-1011 Commented chart of accounts"),
    (EVENT_D1101, "D-1101 Monthly trial balance"),
    (EVENT_D1106, "D-1106 Technical-reserve investments"),
    (EVENT_D1121, "D-1121 Deductions"),
    (EVENT_D1198, "D-1198 Period reopening"),
    (EVENT_D1199, "D-1199 Monthly closing"),
]

RETURN_D9001 = "D-9001"
RETURN_D9101 = "D-9101"
RETURN_D9106 = "D-9106"
RETURN_D9112 = "D-9112"
RETURN_D9121 = "D-9121"
RETURN_D9198 = "D-9198"
RETURN_D9199 = "D-9199"
RETURN_D9209 = "D-9209"

RETURN_TYPES = [
    (RETURN_D9001, "D-9001 Table-event return"),
    (RETURN_D9101, "D-9101 Trial-balance return"),
    (RETURN_D9106, "D-9106 Technical-reserve return"),
    (RETURN_D9112, "D-9112 Deductions return"),
    (RETURN_D9121, "D-9121 Public-bond operations return"),
    (RETURN_D9198, "D-9198 Reopening return"),
    (RETURN_D9199, "D-9199 Monthly closing return"),
    (RETURN_D9209, "D-9209 Transactional return"),
]
RETURN_TYPE_BY_TAG = {
    "evtRetornoTabela": RETURN_D9001,
    "evtRetornoBalan": RETURN_D9101,
    "evtRetornoAplicFin": RETURN_D9106,
    "evtRetornoRDed": RETURN_D9112,
    "evtRetornoTitPub": RETURN_D9121,
    "evtRetornoReabert": RETURN_D9198,
    "evtRetornoMensal": RETURN_D9199,
    "evtRetornoTransac": RETURN_D9209,
}

TABLE_EVENTS = (EVENT_D1001, EVENT_D1011)
PERIODIC_EVENTS = (EVENT_D1198, EVENT_D1101, EVENT_D1106, EVENT_D1121, EVENT_D1199)
PRIMARY_ACTIONS = [
    ("generate_tables", "Generate Tables"),
    ("send_tables", "Send Tables"),
    ("generate_trial", "Generate Trial Balance"),
    ("generate_d1106", "Generate D-1106"),
    ("load_deductions", "Load Deductions"),
    ("generate_d1121", "Generate D-1121"),
    ("close_period", "Close Period"),
    ("send_periodics", "Send Periodics"),
    ("consult", "Consult Results"),
    ("reopen", "Reopen Period"),
    ("replace_tables", "Replace Tables"),
    ("replace_trial", "Replace Trial Balance"),
    ("replace_d1106", "Replace D-1106"),
    ("replace_d1121", "Replace D-1121"),
    ("rectify_d1121", "Rectify D-1121"),
]
STRUCTURED_EVENT_ID = TABLE_EVENTS + PERIODIC_EVENTS
STRUCTURED_EVENT_ID_RE = r"^DeRE[0-9]{4}1[0-9A-Z]{14}[0-9]{19}$"
D1199_RECEIPT_RE = r"^[0-9]{4}-20[0-9]{2}(?:0[1-9]|1[0-2])-[0-9A-Z]{19}$"

NS = {
    EVENT_D1001: "http://www.dere.gov.br/schemas/evtInfoContrib/v1_0_1",
    EVENT_D1011: "http://www.dere.gov.br/schemas/evtPGCC/v1_0_3",
    EVENT_D1101: "http://www.dere.gov.br/schemas/evtBalancete/v1_0_1",
    EVENT_D1106: "http://www.dere.gov.br/schemas/evtAplicResTec/v1_0_0",
    EVENT_D1121: "http://www.dere.gov.br/schemas/evtRelDeducoes/v0_0_1",
    EVENT_D1198: "http://www.dere.gov.br/schemas/evtReabertMensal/v0_0_1",
    EVENT_D1199: "http://www.dere.gov.br/schemas/evtFechMensal/v0_0_2",
    "lote": "http://www.dere.gov.br/schemas/envioLoteDere/v1_0_1",
}

DFE_TYPE_BY_DOCUMENT = {
    "55": "03",
    "65": "04",
    "SE": "02",
}
DEFAULT_TP_ATIV_BY_REGIME = {
    "2": "06",
    "3": "07",
}
DEDUCTION_DOCUMENT_EXCLUDED_STATES = (
    "cancelada",
    "denegada",
    "rejeitada",
    "inutilizada",
)

TOKEN_URL_PROD = "https://api.receitafederal.gov.br/token"
API_URL_RESTRICTED = "https://api.receitafederal.gov.br/prr-dere"
API_URL_PROD = "https://api.receitafederal.gov.br/prr-dere"
DEFAULT_API_URL = API_URL_RESTRICTED
DEFAULT_API_PATH = "/v1/recepcao/lotes"
DEFAULT_CONSULT_PATH = "/v1/consulta/lotes/{protocol}"
DEFAULT_VER_APLIC = "odoo-dere-18.0"
PROTOCOL_RE = r"^[12]\.\d{6}\.\d{1,19}$"
TRANSIENT_HTTP_CODES = frozenset({429, 502, 503, 504})
EVENT_ID_INSCRIPTION_TYPE = "1"
BRASILIA_TZ = "America/Sao_Paulo"

CODTRIB_D1106 = frozenset(
    {
        "120130001",
        "120230001",
        "120330001",
        "111112701",
    }
)
CODTRIB_D1121 = frozenset(
    {
        "110211611",
        "110324611",
        "110324801",
        "111111622",
        "111112612",
        "111112614",
        "111126103",
        "111270002",
        "111290001",
        "111361003",
        "411011105",
        "411012101",
        "411021111",
        "411021211",
        "411031211",
        "411031281",
        "411031411",
        "411032411",
        "411051101",
        "120161002",
        "120161006",
        "120161007",
        "120261002",
        "120261005",
        "120261006",
        "120261099",
        "120361002",
        "120361005",
        "120361006",
        "120361099",
        "120420001",
        "220420002",
        "230161002",
        "431300002",
    }
)
