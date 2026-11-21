# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RtcLegalBasis(models.Model):
    """Legal basis attached to a cClassTrib (LC 214/2025 and annexes)."""

    _name = "l10n_br_fiscal.rtc.legal.basis"
    _description = "RTC legal basis"
    _order = "name"

    name = fields.Char(required=True)
    text = fields.Text()
    normative_reference = fields.Char()

    date_start = fields.Date(required=True)
    date_end = fields.Date()
