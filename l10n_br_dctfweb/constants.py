# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Domain of the MIT import layout, version 1.0.

Every selection here is a closed domain published by the tax authority in the
MIT JSON import layout (ADE CORAT 19/2024, rectified on 2025-02-20). The keys
are the very numbers the payload carries, so the serializer never translates a
label: it writes ``int(key)``.
"""

# Tax groups of the MIT, in the order the layout requires them to be written.
# The value is the JSON object name inside "Debitos".
MIT_GROUP_JSON_KEY = {
    "irpj": "Irpj",
    "csll": "Csll",
    "irrf": "Irrf",
    "ipi": "Ipi",
    "iof": "Iof",
    "pis_pasep": "PisPasep",
    "cofins": "Cofins",
    "other_contributions": "ContribuicoesDiversas",
    "cpss": "Cpss",
    "ret": "RetPagamentoUnificado",
}

MIT_GROUP = [
    ("irpj", "IRPJ"),
    ("csll", "CSLL"),
    ("irrf", "IRRF"),
    ("ipi", "IPI"),
    ("iof", "IOF"),
    ("pis_pasep", "PIS/PASEP"),
    ("cofins", "COFINS"),
    ("other_contributions", "Other contributions"),
    ("cpss", "CPSS"),
    ("ret", "RET/Unified payment"),
]

# The layout has no periodicity field: it drives which extra fields a debit
# needs (PaDebito, TrimPostergado, AnoDebito). Codes are the manual's.
MIT_PERIODICITY = [
    ("daily", "Daily"),
    ("ten_day", "Ten-day"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("annual", "Annual"),
]

MIT_MONTH = [
    ("1", "January"),
    ("2", "February"),
    ("3", "March"),
    ("4", "April"),
    ("5", "May"),
    ("6", "June"),
    ("7", "July"),
    ("8", "August"),
    ("9", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
]

# DadosIniciais.QualificacaoPj
MIT_PJ_QUALIFICATION = [
    ("1", "Legal entity in general"),
    (
        "2",
        "Development agency, bank or other legal entity under art. 22, "
        "paragraph 1, of Law 8.212/1991",
    ),
    ("3", "Credit cooperative"),
    ("4", "Insurance brokerage company"),
    (
        "5",
        "Insurance or capitalization company, or for-profit open "
        "supplementary pension entity",
    ),
    (
        "6",
        "Closed supplementary pension entity, or non-profit open "
        "supplementary pension entity",
    ),
    ("7", "Cooperative society"),
    ("8", "Agricultural production or consumer cooperative society"),
    ("9", "Public agency or foundation"),
    (
        "10",
        "State-owned company, mixed-capital company or legal entity under "
        "art. 34, III, of Law 10.833/2003",
    ),
    (
        "11",
        "State, Federal District, municipality or direct public " "administration body",
    ),
    ("12", "More than one qualification during the month"),
]

# DadosIniciais.TributacaoLucro
MIT_PROFIT_TAXATION = [
    ("1", "Annual actual profit"),
    ("2", "Quarterly actual profit"),
    ("3", "Presumed profit"),
    ("4", "Arbitrated profit"),
    ("5", "IRPJ immune"),
    ("6", "IRPJ exempt"),
    ("7", "Simples Nacional"),
]

# DadosIniciais.VariacoesMonetarias
MIT_MONETARY_VARIATION = [
    ("1", "Cash basis"),
    ("2", "Accrual basis"),
    ("3", "Cash basis, high exchange rate volatility"),
]

# DadosIniciais.RegimePisCofins
MIT_PIS_COFINS_REGIME = [
    ("1", "Non-cumulative"),
    ("2", "Cumulative"),
    ("3", "Non-cumulative and cumulative"),
    ("4", "Not applicable"),
]

# ListaEventosEspeciais.TipoEvento
MIT_SPECIAL_EVENT = [
    ("1", "Termination"),
    ("2", "Merger"),
    ("3", "Full spin-off"),
    ("4", "Partial spin-off"),
    ("5", "Absorption (absorbed)"),
    ("6", "Absorption (absorbing)"),
]

# ListaSuspensoes.TipoSuspensao
MIT_SUSPENSION_TYPE = [
    ("1", "Administrative"),
    ("2", "Judicial"),
]

# ListaSuspensoes.MotivoSuspensao. The layout skips 3, 6 and 7: the enum in the
# JSON schema is [1, 2, 4, 5, 8, 9, 10, 11, 12, 13].
MIT_SUSPENSION_REASON = [
    ("1", "Injunction in writ of mandamus"),
    ("2", "Judicial deposit of the full amount"),
    ("4", "Preliminary injunction"),
    ("5", "Injunction in precautionary measure"),
    ("8", "Writ of mandamus ruling favourable to the taxpayer"),
    ("9", "Ordinary action ruling favourable to the taxpayer, upheld by the TRF"),
    ("10", "TRF decision favourable to the taxpayer"),
    ("11", "STJ special appeal decision favourable to the taxpayer"),
    ("12", "STF extraordinary appeal decision favourable to the taxpayer"),
    ("13", "First instance ruling not final, with suspensive effect"),
]

# Groups whose debits may carry a CnpjScp (manual, item 4.2, III).
MIT_SCP_GROUPS = ("irpj", "csll", "pis_pasep", "cofins")

# Revenue code that identifies gold as a financial asset (manual, item 4.2, IV).
MIT_GOLD_CODE = "402802"

# The two codes the manual excludes from the establishment/incorporation rule
# (manual, item 4.2, I and II).
MIT_OTHER_CONTRIBUTIONS_NO_ESTABLISHMENT = "919701"
MIT_RET_NO_INCORPORATION = "617701"

# Extension of a postponed IRPJ/CSLL debit (layout, AnoPostergado).
MIT_POSTPONED_EXTENSION = "10"
