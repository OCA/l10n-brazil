# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp.addons.decimal_precision as dp
from odoo import api, fields, models

PAYMENT_SELECTION = [
    ("boleto", "Boleto"),
    ("cartao", "Cartão"),
    ("cheque", "Cheque"),
    ("dinheiro", "Dinheiro"),
    ("outros", "Outros"),
]


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    payment_mode_selection = fields.Selection(
        selection=PAYMENT_SELECTION, string="Modo de Pagamento"
    )

    has_interest = fields.Boolean(string="Juros?", default=False)

    interest_rate = fields.Float(
        string="Taxa de Juros(%)", digits=dp.get_precision("Account"), default=0.0
    )

    interest_account_id = fields.Many2one(
        comodel_name="account.account", string="Conta", help="Conta padrão para Juros"
    )

    @api.onchange("payment_mode_selection")
    def _onchange_payment_mode(self):
        if self.payment_mode_selection not in ["cartao"]:
            self.has_interest = False

    @api.onchange("has_interest")
    def _onchange_has_interest(self):
        if not self.has_interest:
            self.interest_rate = 0
