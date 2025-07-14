# Copyright 2025 - Escodoo, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0)
from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [
        _name,
        "l10n_br_fiscal.document.mixin.methods",
        "l10n_br_account.decorator.mixin",
    ]

    def _reverse_moves(self, default_values_list=None, cancel=False):
        new_moves = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )

        payment_mode_id = False
        if self.env.context.get("payment_mode_id"):
            payment_mode_id = self.env["account.payment.mode"].browse(
                self.env.context.get("payment_mode_id")
            )
        for move in new_moves:
            move.payment_mode_id = payment_mode_id

        return new_moves
