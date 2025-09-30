# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

NFE_VERSIONS = [("1.10", "1.10"), ("2.00", "2.00"), ("3.10", "3.10"), ("4.00", "4.00")]


NFE_VERSION_DEFAULT = "4.00"

DANFE_INVOICE_DISPLAY = [
    ("full_details", "Full Details"),
    ("duplicates_only", "Duplicates Only"),
]

DANFE_INVOICE_DISPLAY_DEFAULT = "full_details"

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
