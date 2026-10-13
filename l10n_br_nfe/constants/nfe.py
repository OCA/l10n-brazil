# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_ICMS_FCP_ST,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_ICMS_ST,
    TAX_DOMAIN_II,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ISSQN_WH,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_ST,
)

NFE_VERSIONS = [("1.10", "1.10"), ("2.00", "2.00"), ("3.10", "3.10"), ("4.00", "4.00")]


NFE_VERSION_DEFAULT = "4.00"

DANFE_INVOICE_DISPLAY = [
    ("full_details", "Full Details"),
    ("duplicates_only", "Duplicates Only"),
]

DANFE_INVOICE_DISPLAY_DEFAULT = "full_details"

DANFE_RECEIPT_POSITIONS = [("top", "Top"), ("bottom", "Bottom")]

DANFE_RECEIPT_POSITION_DEFAULT = "top"

DANFE_FONT_TYPES = [("times", "Times"), ("courier", "Courier")]

DANFE_FONT_TYPE_DEFAULT = "times"

DANFE_FONT_SIZES = [("small", "Small"), ("big", "Big")]

DANFE_FONT_SIZE_DEFAULT = "small"

NFE_ENVIRONMENTS = [("1", "Produção"), ("2", "Homologação")]


NFE_ENVIRONMENT_DEFAULT = "2"


NFE_TRANSMISSIONS = [
    ("1", "Emissão Normal"),
    ("2", "Contingência FS-IA"),
    ("3", "Contingência SCAN"),
    ("4", "Contingência EPEC"),
    ("5", "Contingência FS-DA"),
    ("6", "Contingência SVC-AN"),
    ("7", "Contingência SVC-RS"),
    ("9", "Contingência off-line da NFC-e"),
]


NFE_TRANSMISSION_DEFAULT = "1"


NFE_DANFE_LAYOUTS = [
    ("0", "Sem geração de DANFE;"),
    ("1", "DANFE normal, Retrato;"),
    ("2", "DANFE normal, Paisagem;"),
    ("3", "DANFE Simplificado;"),
]


NFE_DANFE_LAYOUT_DEFAULT = "1"


NFCE_DANFE_LAYOUTS = [
    ("4", "DANFE NFC-e;"),
    ("5", "DANFE NFC-e por email"),
]


NFCE_DANFE_LAYOUT_DEFAULT = "4"


FISCAL_PAYMENT_MODE = [
    ("01", "01 - Dinheiro"),
    ("02", "02 - Cheque"),
    ("03", "03 - Cartão de Crédito"),
    ("04", "04 - Cartão de Débito"),
    ("05", "05 - Crédito de Loja"),
    ("10", "10 - Vale Alimentação"),
    ("11", "11 - Vale Refeição"),
    ("12", "12 - Vale Presente"),
    ("13", "13 - Vale Combustível"),
    ("14", "14 - Duplicata Mercanti"),
    ("15", "15 - Boleto Bancário"),
    ("16", "16 - Depósito Bancário"),
    ("17", "17 - Pagamento Instantâneo (PIX)"),
    ("18", "18 - Transferência bancária, Carteira Digital"),
    ("19", "19 - Programa de fidelidade, Cashback, Crédito Virtual"),
    ("90", "90 - Sem Pagamento"),
    ("99", "99 - Outros"),
]


# Credit and debit notes (NT 2025.002)

# cClassTrib of the credit and debit note types that require one, the other
# types accept any classification (rules UB14-70 and UB14-80). These
# classifications are only accepted in their note types (rule UB14-60).
NFE_DEBIT_NOTE_TAX_CLASSIFICATION = {
    "01": "800002",
    "02": "811001",
    "03": "811002",
    "05": "800001",
    "07": "410030",
    "08": "811003",
}

NFE_CREDIT_NOTE_TAX_CLASSIFICATION = {
    "02": "810001",
    "05": "800001",
}

# Credit note types that must reference exactly one NF-e (rules B25-30 and
# B25-40) and the one that cannot reference documents (rule B25-65)
NFE_CREDIT_NOTE_TYPES_ONE_REFERENCE = ("01", "03", "04")
NFE_CREDIT_NOTE_TYPES_NO_REFERENCE = ("02",)

# Tax groups of the NF-e item and the taxes they inform. A credit or debit
# note only informs IBS and CBS, except the types below (rule B25-80).
NFE_TAX_GROUP_DOMAINS = {
    "nfe40_ICMS": (
        TAX_DOMAIN_ICMS,
        TAX_DOMAIN_ICMS_SN,
        TAX_DOMAIN_ICMS_ST,
        TAX_DOMAIN_ICMS_FCP,
        TAX_DOMAIN_ICMS_FCP_ST,
    ),
    "nfe40_ICMSUFDest": (TAX_DOMAIN_ICMS,),
    "nfe40_IPI": (TAX_DOMAIN_IPI,),
    "nfe40_II": (TAX_DOMAIN_II,),
    "nfe40_ISSQN": (TAX_DOMAIN_ISSQN, TAX_DOMAIN_ISSQN_WH),
    "nfe40_PIS": (TAX_DOMAIN_PIS,),
    "nfe40_PISST": (TAX_DOMAIN_PIS_ST,),
    "nfe40_COFINS": (TAX_DOMAIN_COFINS,),
    "nfe40_COFINSST": (TAX_DOMAIN_COFINS_ST,),
}

NFE_CREDIT_NOTE_TYPES_WITH_TAXES = ("03", "04", "06")
NFE_DEBIT_NOTE_TYPES_WITH_TAXES = ("07",)

# The advance payment debit note also informs IPI, and PIS and COFINS when
# issued in 2026 (rule B25-80, exceptions 2 and 3)
NFE_DEBIT_NOTE_ADVANCE_PAYMENT = "06"
NFE_DEBIT_NOTE_ADVANCE_PAYMENT_TAX_GROUPS = ("nfe40_IPI",)
NFE_DEBIT_NOTE_ADVANCE_PAYMENT_TAX_GROUPS_2026 = (
    "nfe40_PIS",
    "nfe40_PISST",
    "nfe40_COFINS",
    "nfe40_COFINSST",
)
