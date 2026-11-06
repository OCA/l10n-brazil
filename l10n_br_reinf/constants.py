# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Constants of the EFD-Reinf, all taken from the 2.1.2b layout XSD."""

# tpAmb. There is no default on purpose: the taxpayer has to choose the
# environment before any transmission (see res.company._reinf_environment).
REINF_ENVIRONMENT_PRODUCTION = "1"
REINF_ENVIRONMENT_RESTRICTED = "2"

REINF_ENVIRONMENTS = [
    (REINF_ENVIRONMENT_PRODUCTION, "Production"),
    (REINF_ENVIRONMENT_RESTRICTED, "Restricted Production"),
]

# procEmi: 1 is the application of the taxpayer, 2 the governmental one.
REINF_PROC_EMI = "1"

# verProc, the version of the software that generates the event. The layout
# gives it 20 positions, so it has to stay short.
REINF_VERSAO_PROCESSO = "Odoo l10n_br_reinf"

# tpInsc
REINF_INSCRIPTION_CNPJ = "1"
REINF_INSCRIPTION_CPF = "2"

REINF_INSCRIPTION_TYPES = [
    (REINF_INSCRIPTION_CNPJ, "CNPJ"),
    (REINF_INSCRIPTION_CPF, "CPF"),
]

# indRetif
REINF_RECTIFY_ORIGINAL = "1"
REINF_RECTIFY_RECTIFICATION = "2"

REINF_RECTIFY_INDICATORS = [
    (REINF_RECTIFY_ORIGINAL, "Original"),
    (REINF_RECTIFY_RECTIFICATION, "Rectification"),
]

# One selection value per event of the layout. The value is the event code as
# the tax authority names it, so it can be read in the interface and in the
# logs without a translation table.
REINF_EVENT_TYPES = [
    ("R-1000", "R-1000 Taxpayer information"),
    ("R-1050", "R-1050 Related entities"),
    ("R-1070", "R-1070 Administrative and judicial proceedings"),
    ("R-2010", "R-2010 Withholding on services taken"),
    ("R-2020", "R-2020 Withholding on services rendered"),
    ("R-2030", "R-2030 Resources received by a sport association"),
    ("R-2040", "R-2040 Resources passed on to a sport association"),
    ("R-2050", "R-2050 Commercialization of rural production"),
    ("R-2055", "R-2055 Acquisition of rural production"),
    ("R-2060", "R-2060 Social contribution on gross revenue (CPRB)"),
    ("R-2098", "R-2098 Reopening of the R-2000 series"),
    ("R-2099", "R-2099 Closing of the R-2000 series"),
    ("R-3010", "R-3010 Revenue of a sport event"),
    ("R-4010", "R-4010 Payments to an individual"),
    ("R-4020", "R-4020 Payments to a legal entity"),
    ("R-4040", "R-4040 Payments to an unidentified beneficiary"),
    ("R-4080", "R-4080 Withholding on receipt"),
    ("R-4099", "R-4099 Closing and reopening of the R-4000 series"),
    ("R-9000", "R-9000 Event exclusion"),
]

# Functional classification that keeps a batch homogeneous, not the group
# numbering of the MOR: a closing event never travels with a periodic one,
# because the tax authority processes a batch in parallel.
REINF_EVENT_GROUP_TABLE = "table"
REINF_EVENT_GROUP_PERIODIC = "periodic"
REINF_EVENT_GROUP_CLOSING = "closing"
REINF_EVENT_GROUP_EXCLUSION = "exclusion"

REINF_EVENT_GROUPS = [
    (REINF_EVENT_GROUP_TABLE, "Table events"),
    (REINF_EVENT_GROUP_PERIODIC, "Periodic events"),
    (REINF_EVENT_GROUP_CLOSING, "Closing and reopening events"),
    (REINF_EVENT_GROUP_EXCLUSION, "Exclusion events"),
]

REINF_EVENT_TYPE_GROUP = {
    "R-1000": REINF_EVENT_GROUP_TABLE,
    "R-1050": REINF_EVENT_GROUP_TABLE,
    "R-1070": REINF_EVENT_GROUP_TABLE,
    "R-2010": REINF_EVENT_GROUP_PERIODIC,
    "R-2020": REINF_EVENT_GROUP_PERIODIC,
    "R-2030": REINF_EVENT_GROUP_PERIODIC,
    "R-2040": REINF_EVENT_GROUP_PERIODIC,
    "R-2050": REINF_EVENT_GROUP_PERIODIC,
    "R-2055": REINF_EVENT_GROUP_PERIODIC,
    "R-2060": REINF_EVENT_GROUP_PERIODIC,
    "R-2098": REINF_EVENT_GROUP_CLOSING,
    "R-2099": REINF_EVENT_GROUP_CLOSING,
    "R-3010": REINF_EVENT_GROUP_PERIODIC,
    "R-4010": REINF_EVENT_GROUP_PERIODIC,
    "R-4020": REINF_EVENT_GROUP_PERIODIC,
    "R-4040": REINF_EVENT_GROUP_PERIODIC,
    "R-4080": REINF_EVENT_GROUP_PERIODIC,
    "R-4099": REINF_EVENT_GROUP_CLOSING,
    "R-9000": REINF_EVENT_GROUP_EXCLUSION,
}

# maxOccurs of the eventos group of envioLoteEventosAssincrono-v1_00_00.xsd
REINF_BATCH_MAX_EVENTS = 50

REINF_EVENT_STATES = [
    ("draft", "Draft"),
    ("validated", "Validated"),
    ("pending", "Pending Transmission"),
    ("sent", "Sent"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("rectified", "Rectified"),
    ("excluded", "Excluded"),
]

REINF_BATCH_STATES = [
    ("draft", "Draft"),
    ("sent", "Sent"),
    ("processing", "Processing"),
    ("done", "Processed"),
    ("error", "Error"),
]

# tpOcorr of the occurrences returned by the tax authority
REINF_OCCURRENCE_TYPES = [
    ("1", "Error"),
    ("2", "Warning"),
]

# Taxes the Annex I of the manual maps a nature of income to. The aggregated
# one is the single value that carries CSLL, PIS/PASEP and COFINS together
# under one revenue code.
REINF_WITHHOLDING_TAXES = [
    ("irpf", "IRPF"),
    ("irpj", "IRPJ"),
    ("rra", "RRA"),
    ("aggregated", "Aggregated"),
    ("csll", "CSLL"),
    ("cofins", "COFINS"),
    ("pis_pasep", "PIS/PASEP"),
]

# Which withholding flag of the nature of income each tax raises.
REINF_TAX_WITHHOLDING_FLAG = {
    "irpf": "ret_ir",
    "irpj": "ret_ir",
    "rra": "ret_ir",
    "aggregated": "ret_agreg",
    "csll": "ret_csll",
    "cofins": "ret_cofins",
    "pis_pasep": "ret_pp",
}

# The triggering fact differs per tax, which is why the date is per line: the
# income tax on the credit when it precedes the payment, the PCC on the payment.
# A July invoice paid in August splits into two competences.
REINF_TAXES_ON_CREDIT = ("irpf", "irpj", "rra")
REINF_TAXES_ON_PAYMENT = ("csll", "cofins", "pis_pasep", "aggregated")

# Where each withholding of the localization is read from on a move line, and
# which tax of the EFD-Reinf it feeds. The value fields come from
# l10n_br_fiscal.document.line.mixin, which account.move.line delegates to.
REINF_WITHHOLDING_SOURCES = {
    "irpj": ("irpj_wh_value", "irpj_wh_base"),
    "csll": ("csll_wh_value", "csll_wh_base"),
    "cofins": ("cofins_wh_value", "cofins_wh_base"),
    "pis_pasep": ("pis_wh_value", "pis_wh_base"),
}

# Fallback source: the posted tax lines, by fiscal tax group. The *_wh_value
# fields are re-derived by the tax engine on every write, so a document not
# priced by it has them at zero even with the tax accounted.
REINF_TAX_DOMAIN_MAP = {
    "irpj_wh": "irpj",
    "csll_wh": "csll",
    "cofins_wh": "cofins",
    "pis_wh": "pis_pasep",
}

# The three withholdings collectible as a single aggregated value. The rate
# lives on l10n_br_reinf.revenue.code, with validity, because the LC 214/2025
# changes it.
REINF_AGGREGATABLE_TAXES = ("pis_pasep", "cofins", "csll")

# Why a beneficiary may not suffer the withholding the nature prescribes. The
# distinction is fiscal, not cosmetic: a dispensation of the NATURE keeps the
# aggregated code, an exemption or a zero rate OF THE BENEFICIARY does not.
REINF_BENEFICIARY_PROFILES = [
    ("normal", "Normal"),
    ("work_cooperative", "Cooperative of work"),
    ("consumer_cooperative", "Cooperative of consumption"),
    ("exempt", "Exempt"),
    ("zero_rate", "Zero rate"),
    ("judicial", "Suspended by a judicial measure"),
]

# Names of the column Tributo of the Tabela 01 to the vocabulary of the module.
ADMITTED_TAX_NAMES = {
    "IR": "irpj",
    "CSLL": "csll",
    "COFINS": "cofins",
    "PP": "pis_pasep",
    "AGREGADO": "aggregated",
}

# Tolerance of the difference between the aggregated value and the sum of the
# three rounded components. Below it the difference is only shown; above it the
# competence gets an exception.
REINF_AGGREGATE_TOLERANCE = 0.02

# Art. 68 of the Law 9.430/1996: a DARF below this is carried to the next
# competence under the same revenue code. Minimum of COLLECTION, not the
# minimum of WITHHOLDING per payment of the art. 31 par. 3 of the Law
# 10.833/2003.
REINF_DARF_MINIMUM = 10.0

# Second ten-day period of the month after the competence.
REINF_DARF_DUE_DAY = 20

REINF_DARF_STATES = [
    ("draft", "Draft"),
    ("carried", "Carried to the next competence"),
    ("confirmed", "Confirmed"),
    ("reconciled", "Reconciled"),
]

REINF_CALCULATION_STATES = [
    ("draft", "Draft"),
    ("computed", "Computed"),
    ("verified", "Verified"),
    ("closed", "Closed"),
    ("transmitted", "Transmitted"),
]

REINF_CALCULATION_LINE_STATES = [
    ("ok", "Ok"),
    ("divergent", "Divergent"),
    ("excluded", "Excluded"),
]

# The enumerated reasons a payment does not become a plain declaration line.
# The point of the list is that the conference screen never says "something is
# wrong": it says what is wrong and what to do about it.
REINF_EXCEPTION_CRITICAL = ("partner_without_cnpj", "nature_missing")

REINF_EXCEPTION_REASONS = [
    ("partner_without_cnpj", "Beneficiary without CNPJ"),
    ("nature_missing", "Nature of income not set"),
    ("partial_payment", "Partial payment"),
    ("advance_payment", "Advance payment"),
    ("cancelled_after_payment", "Invoice cancelled after the payment"),
    ("prior_period_invoice", "Invoice of a prior period paid in this one"),
    ("payment_without_invoice", "Payment without an invoice"),
    ("simples_beneficiary", "Beneficiary under the Simples Nacional"),
    ("cooperative_csll_only", "Cooperative: CSLL is waived"),
    ("below_minimum", "Withholding below the minimum to collect"),
    ("judicial_suspension", "Withholding suspended by a judicial decision"),
    ("aggregate_divergence", "Aggregated withholding diverges from its parts"),
    ("aggregate_rate_missing", "Aggregated revenue code without a rate to check"),
    ("aggregate_partial_not_structural", "Aggregate refused: partial withholding"),
    ("cooperative_csll_withheld", "CSLL withheld from a cooperative of work"),
]

# The ind_classif column of the Annex I.
REINF_CLASSIFICATION_INDICATORS = [
    ("yes", "Yes"),
    ("no", "No"),
    ("na", "Not applicable"),
]

# Periodicity of a revenue code (CR). It says which totalizer group of the
# R-9015 carries the code: CRDia, CRSem, CRQui, CRDec or CRMen.
REINF_REVENUE_PERIODICITIES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("fortnightly", "Fortnightly"),
    ("ten_day", "Ten-day"),
    ("monthly", "Monthly"),
]
