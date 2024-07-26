# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import BR_CODES_PAYMENT_ORDER


class AccountMovePaymentModeWizard(models.TransientModel):
    _name = "account.move.payment.mode.cnab.change"
    _description = "Account Move Payment Mode CNAB Wizard"

    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        required=True,
        domain=lambda self: [("payment_method_code", "in", BR_CODES_PAYMENT_ORDER)],
    )

    def set_payment_mode(self):
        move_id = self.env.context.get("active_id")
        move = self.env["account.move"].browse(move_id)
        if move.state == "posted":
            move.payment_mode_id = self.payment_mode_id
            move.load_cnab_info()
