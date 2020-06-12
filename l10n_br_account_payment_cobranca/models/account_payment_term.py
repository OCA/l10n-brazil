# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models
from odoo.exceptions import Warning as UserError

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

    discount_perc = fields.Float(
        string=u"Percentual de Desconto até a Data de Vencimento",
        digits=dp.get_precision('Account'))
    instrucao_discount_perc = fields.Text(
        u'Instrução de Desconto antes do Vencimento',
        help=u'Percentual de Desconto concedido antes da Data de Vencimento',
        default=u'CONCEDER ABATIMENTO PERCENTUAL DE '
    )

    @api.constrains('discount_perc')
    def _check_discount_perc(self):
        for record in self:
            if record.discount_perc > 100 or record.discount_perc < 0:
                raise UserError(
                    _('O percentual deve ser um valor entre 0 a 100.'))


    @api.onchange("payment_mode_selection")
    def _onchange_payment_mode(self):
        if self.payment_mode_selection not in ["cartao"]:
            self.has_interest = False

    @api.onchange("has_interest")
    def _onchange_has_interest(self):
        if not self.has_interest:
            self.interest_rate = 0
