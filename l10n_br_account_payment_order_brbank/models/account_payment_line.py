# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    pix_copy_paste = fields.Char(string="Pix Copy and Paste", copy=False)

    def _check_pix_transfer_type(self):
        """The code carries the receiver: no key or bank account is needed."""
        return super(
            AccountPaymentLine, self.filtered(lambda line: not line.pix_copy_paste)
        )._check_pix_transfer_type()
