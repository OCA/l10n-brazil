# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dataclasses import dataclass
from datetime import date, datetime, timezone

from psycopg2 import OperationalError
from psycopg2.errorcodes import SERIALIZATION_FAILURE

from odoo import fields


def tax_authority_date_to_utc(value):
    """Convert a date of the tax authority answer into a UTC naive string.

    The answer carries the local time with an offset (for example
    2026-10-02T10:15:00-03:00, or -04:00 in MT/AM), but the Datetime fields keep
    naive UTC. A value without offset is kept as it is.
    """
    if not value:
        return False
    if not isinstance(value, datetime):
        if hasattr(value, "to_datetime"):  # xsdata XmlDateTime
            value = value.to_datetime()
        else:
            value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return fields.Datetime.to_string(value)


# Context key of the import: it never creates a product, a unit, an NCM, a CEST or a
# CFOP that the file mentions and the database does not have.
EDI_IMPORT_NO_CREATE = "edi_import_no_create"
# context key of the import of the demo data, which holds locks on the table
EDI_IMPORT_DEMO = "edi_import_demo"


class EdiImportConcurrencyError(OperationalError):
    """The note was imported by a transaction that committed after this one began.

    The transaction cannot see that document (its snapshot is older), so it cannot
    answer that the note was already imported. Raised as a serialization failure,
    which makes the framework roll back and run the call again in a new transaction,
    where the document exists."""

    pgcode = SERIALIZATION_FAILURE


@dataclass(frozen=True)
class EdiParsedFile:
    """What a reader found in a fiscal file, before anything is created."""

    reader: str  # "nfe" | "cte" | "nfse" | "mdfe"
    document_type_code: str  # "55" | "57" | "SE" | "58"
    access_key: str  # only digits, 44 or 50
    issuer_vat: str  # only digits
    # ((role, digits), ...) in priority order; role in
    # ("recipient", "taker", "issuer")
    company_vats: tuple
    status: str  # "authorized" | "cancelled" | "denied" | "unknown"
    status_code: str  # cStat or ""
    binding: object  # what the reader needs in _edi_import_create
    file_name: str
    content: bytes


@dataclass(frozen=True)
class EdiInstallment:
    number: str  # "001", "002"
    date_due: date
    amount: float  # positive, in the currency of the document


@dataclass(frozen=True)
class EdiPayment:
    means: str  # tPag; "" = unknown; "90" = no payment
    amount: float
    term: str  # "cash" | "installments"  (indPag 0 / 1)
    description: str = ""  # xPag when tPag = "99"
    label: str = ""  # name of the means, for the page of the payments


@dataclass(frozen=True)
class EdiLot:
    name: str
    quantity: float  # in the unit declared by the line
    date_manufacture: date | None
    date_expiry: date | None


@dataclass(frozen=True)
class EdiPartnerData:
    """What the file declares about a partner (issuer, recipient, taker, carrier)."""

    role: str  # "issuer" | "recipient" | "taker" | "carrier"
    vat: str = ""  # only digits; "" when the file carries no CNPJ nor CPF
    name: str = ""  # razao social
    state_tax_number: str = ""  # inscricao estadual
    street: str = ""
    street_number: str = ""
    district: str = ""
    zip_code: str = ""
    city: str = ""
    state_code: str = ""
