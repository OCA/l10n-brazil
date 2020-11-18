# © 2012 KMEE INFORMATICA LTDA
#   @author  Daniel Sadamo Hirayama <daniel.sadamo@kmee.com.br>
#   @author  Hugo Uchôas Borges <hugo.borges@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):

        # TODO - Rodando 2 For para não chamar o super em caso do
        #  metodo de pagto ser CNAB, necessário devido o problema abaixo
        for rec in self:
            if rec.payment_method_code in ('240', '400', '500'):
                # TODO - Idealmente isso deveria ser resolvido com um
                #  domain=[('code', 'not in', ('400','240','500'))]
                #  no campo payment_method_id, mas mesmo adicionando isso na
                #  visão ou sobre escrevendo o campo não funciona e não gera
                #  erros, não consegui identificar o motivo do problema (
                #  seria algum problema no orm ? Não encontrei um issue aberto
                #  com referencia a isso ), para reproduzir o erro basta tentar
                #  incluir o domain no campo como comentado acima e testar
                #  na tela.
                #  Testar na migração.
                raise UserError(_(
                    "CNAB Payment Method can't be used to make"
                    ' direct Payments, just used in Payment Orders,'
                    ' choose another one.'))
        super().post()
        for record in self:
            record.invoice_ids.create_account_payment_line_baixa(record.amount)
