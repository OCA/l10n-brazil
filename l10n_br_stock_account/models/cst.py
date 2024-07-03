# Copyright (C) 2024 - Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class CST(models.Model):
    _inherit = "l10n_br_fiscal.cst"

    default_creditable_tax = fields.Boolean(
        string="Creditable Tax Default?",
        default=True,
        help="Defines default value for creditable tax boolean for tax_ids that have"
        "self as CST In",
    )
