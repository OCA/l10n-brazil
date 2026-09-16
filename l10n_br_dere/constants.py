# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

EVENT_D1001 = "D-1001"
EVENT_D1011 = "D-1011"
EVENT_D1101 = "D-1101"
EVENT_D1106 = "D-1106"
EVENT_D1121 = "D-1121"
EVENT_D1198 = "D-1198"
EVENT_D1199 = "D-1199"
EVENT_D9001 = "D-9001"
EVENT_D9101 = "D-9101"
EVENT_D9199 = "D-9199"

EVENT_TYPES = [
    (EVENT_D1001, "D-1001 Taxpayer information"),
    (EVENT_D1011, "D-1011 Commented chart of accounts"),
    (EVENT_D1101, "D-1101 Monthly trial balance"),
    (EVENT_D1106, "D-1106 Technical-reserve investments"),
    (EVENT_D1121, "D-1121 Deductions"),
    (EVENT_D1198, "D-1198 Period reopening"),
    (EVENT_D1199, "D-1199 Monthly closing"),
    (EVENT_D9001, "D-9001 Table-event return"),
    (EVENT_D9101, "D-9101 Trial-balance return"),
    (EVENT_D9199, "D-9199 Closing return"),
]

TABLE_EVENTS = (EVENT_D1001, EVENT_D1011)
PERIODIC_EVENTS = (EVENT_D1198, EVENT_D1101, EVENT_D1106, EVENT_D1121, EVENT_D1199)
STRUCTURED_EVENT_ID = (EVENT_D1101, EVENT_D1198, EVENT_D1199)
STRUCTURED_EVENT_ID_RE = r"^DeRE[0-9]{4}[1-2][0-9A-Z]{14}[0-9]{19}$"
D1199_RECEIPT_RE = r"^[0-9]{4}-20[0-9]{2}(?:0[1-9]|1[0-2])-[0-9A-Z]{19}$"

NS = {
    EVENT_D1001: "http://www.dere.gov.br/schemas/evtInfoContrib/v1_0_1",
    EVENT_D1011: "http://www.dere.gov.br/schemas/evtPGCC/v1_0_3",
    EVENT_D1101: "http://www.dere.gov.br/schemas/evtBalancete/v1_0_1",
    EVENT_D1198: "http://www.dere.gov.br/schemas/evtReabertMensal/v0_0_1",
    EVENT_D1199: "http://www.dere.gov.br/schemas/evtFechMensal/v0_0_2",
    "lote": "http://www.dere.gov.br/schemas/envioLoteDere/v1_0_1",
}

TOKEN_URL_PROD = "https://api.receitafederal.gov.br/token"
DEFAULT_API_URL = "https://api.receitafederal.gov.br"
DEFAULT_VER_APLIC = "odoo-l10n-br-dere-18.0"
DEFAULT_CONSULT_PATH = "/dere/v1/consulta/lotes/{protocol}"
