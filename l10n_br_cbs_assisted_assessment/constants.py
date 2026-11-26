# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_assisted_assessment.constants import (
    SERVICE_CREDITS,
    SERVICE_DEBITS,
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
)

ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_RESTRICTED = "restricted"
ENVIRONMENTS = [
    (ENVIRONMENT_RESTRICTED, "Restricted Production"),
    (ENVIRONMENT_PRODUCTION, "Production"),
]

DEFAULT_TOKEN_URL = "https://api.receitafederal.gov.br/token"
DEFAULT_API_URL = "https://api.receitafederal.gov.br"

# Both environments share the host and differ only in the path prefix.
ENVIRONMENT_PATH = {
    ENVIRONMENT_PRODUCTION: "/apuracao-cbs/v2",
    ENVIRONMENT_RESTRICTED: "/apuracao-cbs-prr/v2",
}

SERVICE_PATH = {
    SERVICE_DEBITS: "debitos",
    SERVICE_CREDITS: "creditos",
    SERVICE_PAYMENTS: "pagamentos",
    SERVICE_WITHHOLDINGS: "recolhimentos",
}

# Services whose file is a DARF composition, not an assessment line.
PAYMENT_SERVICES = (SERVICE_PAYMENTS, SERVICE_WITHHOLDINGS)

# Opened by the daily cron. It stays inactive until a company opts in.
DAILY_SERVICES = (
    SERVICE_DEBITS,
    SERVICE_CREDITS,
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
)

PAYMENT_TYPE_RAD = "1"
PAYMENT_TYPE_PCONT = "2"
PAYMENT_TYPES = [
    (PAYMENT_TYPE_RAD, "RAD"),
    (PAYMENT_TYPE_PCONT, "PCONT"),
]
STATUS_PATH = "situacao"
DOWNLOAD_PATH = "download"

# The collection holding the values of each service in the downloaded file.
SERVICE_COLLECTION = {
    SERVICE_DEBITS: "debitos",
    SERVICE_CREDITS: "creditos",
}

STATE_CONCLUDED = "CONCLUIDA"
STATE_ERROR = "ERRO"

REQUEST_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 300

WEBHOOK_ROUTE = "/l10n_br_cbs_assessment/webhook"

# Requests are polled as a recovery path, because the callback is not always
# delivered by the gateway.
POLL_LIMIT = 50
