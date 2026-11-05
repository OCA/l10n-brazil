# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# The NFS-e Nacional foreign trade group (tpMoeda, type TSCodMoeda) asks for
# the numeric currency code of the BACEN table (xs:pattern [0-9]{3}, see
# nfelib/nfse/schemas/v1_0/tiposSimples_v1.00.xsd). Keyed by ISO 4217 code,
# which is what ``res.currency.name`` holds. Codes confirmed against the BCB
# currency table (https://www4.bcb.gov.br/Download/fechamento/M<date>.csv,
# 2026-11-04). Currencies not listed here are exported without the code, so
# the user is not sent a wrong one.
CURRENCY_BACEN_CODE = {
    "USD": "220",
    "EUR": "978",
    "GBP": "540",
    "JPY": "470",
    "CHF": "425",
    "CAD": "165",
    "AUD": "150",
    "CNY": "795",
    "ARS": "706",
    "CLP": "715",
    "COP": "720",
    "PYG": "450",
    "PEN": "660",
    "UYU": "745",
}
