# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

TRIBUTE_CBS = "cbs"
TRIBUTE_IBS = "ibs"
TRIBUTES = [
    (TRIBUTE_CBS, "CBS"),
    (TRIBUTE_IBS, "IBS"),
]

LINE_DEBIT = "debit"
LINE_CREDIT = "credit"
LINE_TYPES = [
    (LINE_DEBIT, "Debit"),
    (LINE_CREDIT, "Credit"),
]

SERVICE_DEBITS = "debits"
SERVICE_CREDITS = "credits"
SERVICE_PAYMENTS = "payments"
SERVICE_WITHHOLDINGS = "withholdings"
SERVICE_TYPES = [
    (SERVICE_DEBITS, "Debits"),
    (SERVICE_CREDITS, "Credits"),
    (SERVICE_PAYMENTS, "Payments"),
    (SERVICE_WITHHOLDINGS, "Acquirer withholdings"),
]
SERVICE_LINE_TYPE = {
    SERVICE_DEBITS: LINE_DEBIT,
    SERVICE_CREDITS: LINE_CREDIT,
}

# A request that has already been opened at the gateway must be downloaded or
# applied before another call of the same service is made, because each opening
# consumes the daily quota.
OPEN_REQUEST_STATES = ("requested", "notified", "downloaded")

# Art. 46 of Decree 12,955/2026 (CBS) and CGIBS Resolution 6/2026 (IBS): the tax
# administration presents the assessment by the 15th day of the following month,
# or by the 20th for taxpayers required to file the DeRE.
AVAILABILITY_DAY = 15
AVAILABILITY_DAY_DERE = 20

# Daily limit of the request opening endpoint, per the common rules of the
# asynchronous assessment APIs. Exceeding it answers HTTP 429.
DAILY_REQUEST_QUOTA = 100

# The signed download URL delivered by the webhook is valid for 48 hours.
SIGNED_URL_HOURS = 48

# Days before the deadline when the responsible user starts being warned. Silence
# until the deadline constitutes the tax credit (LC 214/2025, art. 46, § 4).
DEADLINE_WARNING_DAYS = 5

# NFS-e access keys are longer than the 44 digits of the NF-e.
DOCUMENT_KEY_SIZE = 50

DIVERGENCE_VALUE = "value"
DIVERGENCE_MISSING_LOCAL = "missing_local"
DIVERGENCE_MISSING_FISCO = "missing_fisco"
DIVERGENCE_CREDIT_DENIED = "credit_denied"
DIVERGENCE_TYPES = [
    (DIVERGENCE_VALUE, "Different value"),
    (DIVERGENCE_MISSING_LOCAL, "Document only in the assessment"),
    (DIVERGENCE_MISSING_FISCO, "Document only in the bookkeeping"),
    (DIVERGENCE_CREDIT_DENIED, "Credit not granted"),
]

ACTION_DEBIT_NOTE = "debit_note"
ACTION_CREDIT_NOTE = "credit_note"
ACTION_FIX_REGISTRATION = "fix_registration"
ACTION_REGISTER_DOCUMENT = "register_document"
ACTION_REVIEW_CREDIT = "review_credit"
SUGGESTED_ACTIONS = [
    (ACTION_DEBIT_NOTE, "Issue debit note"),
    (ACTION_CREDIT_NOTE, "Issue credit note"),
    (ACTION_FIX_REGISTRATION, "Fix the tax registration"),
    (ACTION_REGISTER_DOCUMENT, "Register the missing document"),
    (ACTION_REVIEW_CREDIT, "Review the credit eligibility"),
]

BOOKKEEPING_AWAITING = "awaiting"
BOOKKEEPING_MATCH = "match"
BOOKKEEPING_ONLY_ERP = "only_erp"
BOOKKEEPING_VALUE = "value"
BOOKKEEPING_STATUSES = [
    (BOOKKEEPING_AWAITING, "Awaiting Download"),
    (BOOKKEEPING_MATCH, "Matches"),
    (BOOKKEEPING_ONLY_ERP, "Only in the Bookkeeping"),
    (BOOKKEEPING_VALUE, "Different value"),
]

PER_APUR_RE = r"^20\d{2}-(?:0[1-9]|1[0-2])$"

# Electronic document models reported in the assessment.
DOCUMENT_MODELS = {
    55: "NF-e",
    57: "CT-e",
    62: "NFCom",
    63: "BP-e",
    64: "GTV-e",
    65: "NFC-e",
    66: "NF3-e",
    67: "CT-e OS",
    91: "NFS-e",
    92: "NFS-e Via",
    93: "BP-e TM",
    94: "DeRE",
    97: "CT-e Simplificado",
}

# Debit origins reported in the assessment. Credits report their own origins,
# which are not enumerated in the published documentation.
DEBIT_ORIGINS = {
    0: "Normal",
    20: "Refund by taxpayer payment",
    21: "Refund by acquirer withholding",
    22: "Refund by credit",
    30: "Credit cancellation",
    31: "Acquirer withholding cancellation",
    32: "Taxpayer payment cancellation",
    50: "Perishing in FOB transport",
    51: "Perishing in CIF transport",
    52: "Refund of CIF perishing by taxpayer payment",
    53: "Refund of CIF perishing by acquirer withholding",
    54: "Refund of CIF perishing by credit",
    55: "Credit note for penalty and interest",
}
