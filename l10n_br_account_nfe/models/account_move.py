# Copyright 2025-TODAY Akretion - Raphaẽl Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models
from odoo.tools import frozendict


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_imported_terms(self):
        res = super()._compute_imported_terms()
        if not self.imported_document:
            return res
        for dup in self.nfe40_dup:
            key = frozendict(
                {
                    "move_id": self.id,
                    "date_maturity": dup.nfe40_dVenc,
                    "discount_date": False,
                    "discount_percentage": 0,
                }
            )
            if key not in self.needed_terms:
                self.needed_terms[key] = {
                    "balance": -dup.nfe40_vDup,
                    "amount_currency": -dup.nfe40_vDup,
                }
        return res
