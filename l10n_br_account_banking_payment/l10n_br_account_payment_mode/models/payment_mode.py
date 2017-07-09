# -*- coding: utf-8 -*-
# #############################################################################
#
#    Account Payment Partner module for OpenERP
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    type_sale_payment = fields.Selection(
        [('00', u'00 - Duplicata'),
         ('01', u'01 - Cheque'),
         ('02', u'02 - Promissória'),
         ('03', u'03 - Recibo'),
         ('99', u'99 - Outros')],
        string='Tipo SPED', required=True, default='99')

    type_payment = fields.Selection(
        [('00', u'00 - Duplicata'),
         ('99', u'99 - Outros')],
        string='Tipo SPED', required=True, default='99')

    type_purchase_payment = fields.Selection(
        [('01', u'01 - Crédito em conta-corrente ou poupança Bradesco'),
         ('02', u'02 - Cheque OP ( Ordem de Pagamento'),
         ('03', u'03 - DOC COMPE'),
         ('05', u'05 - Crédito em conta real time'),
         ('08', u'08 - TED'),
         ('30', u'30 - Rastreamento de Títulos'),
         ('31', u'31 - Títulos de terceiros'),
         ]
    )
    internal_sequence_id = fields.Many2one('ir.sequence', u'Sequência')
    instrucoes = fields.Text(u'Instruções de cobrança')
    invoice_print = fields.Boolean(
        u'Gerar relatorio na conclusão da fatura?')

    _sql_constraints = [
        ('internal_sequence_id_unique',
         'unique(internal_sequence_id)',
         u'Sequência já usada! Crie uma sequência unica para cada modo')
    ]


class PaymentModeType(models.Model):
    _inherit = 'payment.mode.type'
    _description = 'Payment Mode Type'

    payment_order_type = fields.Selection(
        selection_add=[
            ('cobranca', u'Cobrança'),
        ])


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    payment_order_type = fields.Selection(
        selection_add=[
            ('cobranca', u'Cobrança'),
        ])
