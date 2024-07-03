# Copyright (C) 2024 - Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    creditable_tax = fields.Boolean(
        string="Creditable Tax?",
        default=lambda self: (
            self.cst_in_id.default_creditable_tax if self.cst_in_id else False
        ),
    )

    @api.onchange("cst_in_id")
    def _onchange_cst_in_id(self):
        if self.cst_in_id:
            self.creditable_tax = self.cst_in_id.default_creditable_tax
