# Copyright (C) 2024 - TODAY Felipe Motter Pereira - Engenere.one
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    disable_tax_entries = fields.Boolean(
        string="Disable Tax Entries",
        help="If checked, no accounting entries for taxes will be generated for "
        "this company.",
    )
