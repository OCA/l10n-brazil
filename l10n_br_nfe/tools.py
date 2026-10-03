# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timezone

from xsdata.models.datatype import XmlDateTime

from odoo import fields


def tax_authority_date_to_utc(value):
    """Convert a date of the tax authority answer into a UTC naive string.

    The answer carries the local time with an offset (for example
    2026-10-02T10:15:00-03:00, or -04:00 in MT/AM), but the Datetime fields keep
    naive UTC. A value without offset is kept as it is.
    """
    if not value:
        return False
    if isinstance(value, XmlDateTime):
        value = value.to_datetime()
    elif not isinstance(value, datetime):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return fields.Datetime.to_string(value)
