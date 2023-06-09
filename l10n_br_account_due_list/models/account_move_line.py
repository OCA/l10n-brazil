# Copyright (C) 2023 - Felipe Motter Pereira - Engenere.one
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models


class AccountInvoice(models.Model):
    _inherit = "account.move.line"

    def action_register_payment(self):
        """Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        """
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": {
                "active_model": "account.move.line",
                "active_ids": self.ids,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
