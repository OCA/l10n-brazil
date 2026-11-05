# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Numeric currency code of the BACEN table (SISBACEN), the one the NFS-e
# foreign trade group (tpMoeda, TSCodMoeda) asks for. Keyed by ISO 4217 code,
# which is what ``res.currency.name`` holds. Currencies not listed here are
# exported without the code, so the user is not sent a wrong one.
CURRENCY_BACEN_CODE = {
    "USD": "220",
    "EUR": "978",
    "GBP": "540",
    "JPY": "470",
    "CHF": "425",
    "CAD": "165",
    "AUD": "150",
    "CNY": "790",
    "ARS": "706",
}
