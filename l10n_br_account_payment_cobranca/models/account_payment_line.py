# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO)


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        mode = (
            self.env['account.payment.order']
            .browse(self.env.context.get('order_id'))
            .payment_mode_id
        )
        if mode.doc_finality_code:
            res.update({'doc_finality_code': mode.doc_finality_code})
        if mode.ted_finality_code:
            res.update({'ted_finality_code': mode.ted_finality_code})
        if mode.complementary_finality_code:
            res.update(
                {'complementary_finality_code': mode.complementary_finality_code}
            )
        if mode.favored_warning:
            res.update({'favored_warning': mode.favored_warning})
        return res

    own_number = fields.Char(string='Nosso Numero')
    document_number = fields.Char(string='Número documento')
    company_title_identification = fields.Char(string='Identificação Titulo Empresa')
    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string='Complemento do Tipo de Serviço',
        help='Campo P005 do CNAB',
    )
    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string='Código Finalidade da TED',
        help='Campo P011 do CNAB',
    )
    complementary_finality_code = fields.Char(
        size=2, string='Código de finalidade complementar', help='Campo P013 do CNAB'
    )
    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string='Aviso ao Favorecido',
        help='Campo P006 do CNAB',
        default='0',
    )
    rebate_value = fields.Float(
        digits=(13, 2),
        string='Valor do Abatimento',
        help='Campo G045 do CNAB',
        default=0.00,
    )
    discount_value = fields.Float(
        digits=(13, 2),
        string='Valor do Desconto',
        help='Campo G046 do CNAB',
        default=0.00,
    )
    interest_value = fields.Float(
        digits=(13, 2), string='Valor da Mora', help='Campo G047 do CNAB', default=0.00
    )
    fee_value = fields.Float(
        digits=(13, 2), string='Valor da Multa', help='Campo G048 do CNAB', default=0.00
    )
