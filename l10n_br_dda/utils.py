# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal


def normalize_cnpj(value):
    """CNPJ (also the alphanumeric one) as upper case text, no punctuation."""
    if not value:
        return ""
    return re.sub(r"[^0-9A-Za-z]", "", str(value)).upper()


def cnpj_root(value):
    """First 8 characters of a full CNPJ, or "" for a CPF or a short value."""
    value = normalize_cnpj(value)
    return value[:8] if len(value) == 14 else ""


def format_cnpj(value):
    value = normalize_cnpj(value)
    if len(value) != 14:
        return value
    return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"


def normalize_digitable_line(value):
    """Digits only (47 for a bank boleto, 48 for a collection document)."""
    return re.sub(r"\D", "", str(value or ""))


def normalize_document_number(value):
    """Digits only, no leading zeros, no installment suffix ("NF-1234/02" -> "1234")."""
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"[/\\]\s*\d{1,3}$", "", text)
    text = re.sub(r"(?<=\d{3})-\d{1,2}$", "", text)
    return re.sub(r"\D", "", text).lstrip("0")


def to_date(value):
    """Accept date, datetime or ISO text; the 0001-01-01 sentinel is None."""
    if not value:
        return None
    if isinstance(value, datetime):
        value = value.date()
    elif isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return None
    if not isinstance(value, date) or value.year <= 1:
        return None
    return value


# Port of brbank (dda.py, simulador/dados.py): same digitable lines as the simulator.
def dv_mod10(field):
    total = 0
    for position, digit in enumerate(reversed(field)):
        product = int(digit) * (2 if position % 2 == 0 else 1)
        total += product - 9 if product > 9 else product
    return (10 - total % 10) % 10


def dv_mod11_barras(base):
    """General check digit of the bar code (43 digits, without the DV)."""
    total = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(base)))
    dv = 11 - total % 11
    return 1 if dv in (0, 10, 11) else dv


def due_factor(due):
    """Due date factor of the boleto (cycle restarted on 2025-02-22, base 1000)."""
    return 1000 + (due - date(2025, 2, 22)).days


def build_digitable_line(bank, amount, due, seed):
    """Bank boleto digitable line (47 digits); the free field hashes `seed`."""
    cents = int((Decimal(str(amount)) * 100).to_integral_value())
    if not 0 < cents < 10**10:
        raise ValueError("amount does not fit the digitable line")
    factor = due_factor(due)
    if not 1000 <= factor <= 9999:
        raise ValueError("due date outside the due date factor")
    free = "".join(str(b % 10) for b in hashlib.sha256(seed.encode()).digest()[:25])
    head = f"{bank}9"
    amount_field = str(factor).zfill(4) + str(cents).zfill(10)
    dv_general = dv_mod11_barras(head + amount_field + free)
    field1, field2, field3 = head + free[:5], free[5:15], free[15:25]
    return (
        f"{field1}{dv_mod10(field1)}"
        f"{field2}{dv_mod10(field2)}"
        f"{field3}{dv_mod10(field3)}"
        f"{dv_general}{amount_field}"
    )
