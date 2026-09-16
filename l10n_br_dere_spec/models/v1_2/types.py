# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

TP_OPER = [
    ("1", "Inclusion"),
    ("2", "Replacement"),
    ("3", "Exclusion"),
]

TP_OPER_CLOSE = [
    ("1", "Inclusion"),
]

TP_AMB = [
    ("1", "Production"),
    ("2", "Restricted production"),
]

APLIC_EMI = [
    ("1", "Company application"),
    ("2", "Government application"),
]

MOT_EXCL = [
    ("1", "Judicial or administrative order"),
    ("2", "Improper submission (inexistent fact)"),
    ("3", "Identification error (CNPJ/period)"),
    ("9", "Other"),
]

REG_TRIB_PRINC = [
    ("1", "Specific regime - Financial services"),
    ("2", "Specific regime - Health-care plans"),
    ("3", "Specific regime - Prize contests"),
    ("9", "Other taxation regimes"),
]

REG_TRIB_SECUND = [
    ("1", "Specific regime - Financial services"),
    ("2", "Specific regime - Health-care plans"),
    ("3", "Specific regime - Prize contests"),
]

IND_NAT_TRIB = [
    ("0", "Regular taxation"),
    ("1", "Immunity or non-incidence"),
]

PLANO_CTA_REF = [
    ("1", "COSIF"),
    ("2", "ANS"),
    ("3", "SUSEP"),
    ("4", "SPED"),
    ("5", "PREVIC"),
]

FREQ_ENCERR = [
    ("A", "Annual"),
    ("S", "Semiannual"),
    ("Q", "Four-monthly"),
    ("T", "Quarterly"),
    ("B", "Bimonthly"),
    ("M", "Monthly"),
]

IND_CTA = [
    ("S", "Synthetic"),
    ("A", "Analytic"),
]

NAT_CTA = [
    ("C", "Credit"),
    ("D", "Debit"),
    ("V", "Variable"),
]

COD_NAT = [
    ("1", "Asset"),
    ("2", "Liability"),
    ("3", "Equity"),
    ("4", "Revenue"),
    ("5", "Expense"),
]

IND_TRIB_ISS = [
    ("0", "Not subject to ISS"),
    ("1", "Subject to ISS"),
]

NAT_SALDO = [
    ("D", "Debit"),
    ("C", "Credit"),
]

CD_RETORNO = [
    ("0", "Error"),
    ("1", "Success"),
]

TIPO_OCORRENCIA = [
    ("1", "Error"),
    ("2", "Warning"),
]

USAR_BCN = [
    ("0", "Do not use accumulated negative base"),
    ("1", "Use accumulated negative base"),
]

METODO_APROVEIT = [
    ("0", "FIFO computed by the tax authority"),
    ("1", "Manual amounts by origin period"),
]
