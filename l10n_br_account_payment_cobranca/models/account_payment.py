# © 2012 KMEE INFORMATICA LTDA
#   @author  Daniel Sadamo Hirayama <daniel.sadamo@kmee.com.br>
#   @author  Hugo Uchôas Borges <hugo.borges@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        super().post()
        for record in self:
            record.invoice_ids.create_account_payment_line_baixa()
