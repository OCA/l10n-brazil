# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timezone

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
