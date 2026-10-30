# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Helpers used to build and to read the FCI digital file."""

import re
from decimal import ROUND_HALF_UP, Decimal

from .constants import FCI_FIELD_SEPARATOR


def compute_import_content(amount_imported, amount_interstate, precision=2):
    """Return the Import Content (Conteúdo de Importação) percentage.

    ``CI = amount_imported / amount_interstate`` expressed in percent. The
    division is done with :class:`~decimal.Decimal` to avoid the float
    representation error changing the rounded result of values whose third
    decimal digit is a 5.
    """
    if not amount_interstate:
        return 0.0
    exponent = Decimal(1).scaleb(-precision)
    result = (
        Decimal(str(amount_imported)) / Decimal(str(amount_interstate)) * Decimal(100)
    )
    return float(result.quantize(exponent, rounding=ROUND_HALF_UP))


def format_amount(value, precision=2):
    """Format an amount as expected by the file: comma as decimal separator,
    no thousand separator."""
    exponent = Decimal(1).scaleb(-precision)
    amount = Decimal(str(value or 0.0)).quantize(exponent, rounding=ROUND_HALF_UP)
    return f"{amount}".replace(".", ",")


def sanitize_text(value, size=None):
    """Remove the field separator and the line breaks from a text field."""
    if not value:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace(FCI_FIELD_SEPARATOR, " ")).strip()
    if size:
        text = text[:size]
    return text


def sanitize_code(value, size=None):
    """Remove every character which is not a letter or a digit."""
    if not value:
        return ""
    code = re.sub(r"[^0-9A-Za-z]", "", str(value))
    if size:
        code = code[:size]
    return code
