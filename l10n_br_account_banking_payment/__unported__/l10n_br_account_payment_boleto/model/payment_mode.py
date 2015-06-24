# -*- encoding: utf-8 -*-
# #############################################################################
#
# Account Payment Partner module for OpenERP
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

from openerp.osv import orm, fields
from tools.translate import _
from datetime import datetime, date
from ..boleto.document import Boleto

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class PaymentModeType(orm.Model):
    _inherit = 'payment.mode.type'

    _columns = {
        'type_payment': fields.selection(
            [('00', 'Duplicata'), ('01', 'Cheque'), ('02', 'Promissória'), ('03', 'Recibo'), ('99', 'Outros')],
            'Tipo SPED', required=True),
    }
    _defaults = {
        'type_payment': '99'
    }


class PaymentMode(orm.Model):
    _inherit = 'payment.mode'

    _columns = {
        'internal_sequence_id': fields.many2one('ir.sequence', 'Sequência'),
        'instrucoes': fields.text('Instruções de cobrança'),
        'invoice_print': fields.boolean('Gerar relatorio na conclusão da fatura?'),
        'boleto_carteira': fields.char('Carteira', size=2),
        'boleto_modalidade': fields.char('Modalidade', size=2),
        'boleto_convenio': fields.char('Codigo convênio', size=10),
        'boleto_variacao': fields.char('Variação', size=2),
        'boleto_cnab_code': fields.char('Codigo Cnab', size=20),
        'boleto_aceite': fields.boolean('Aceite'),
        'type_payment_sped': fields.related('type', 'type_payment', readonly=True, type='char', size=2,
                                            relation='payment.mode.type', string='Tipo SPED'),
    }

class AccountMoveLine(orm.Model):
    _inherit = 'account.move.line'

    _columns = {
        'date_payment_create': fields.date(u'Data da criação do pagamento', readonly=True),
    }

    #### REMOVE THIS TO A THIRD PART MODULE
    # def finalize_payment(self, cr, uid, move_line, context):
    #     return self.boleto_create(cr, uid, move_line, context)

    def send_payment(self, cr, uid, ids, context=None):
        boletoList = []

        for move_line in self.browse(cr, uid, ids):
            try:
                if move_line.payment_mode_id.type.type_payment == '00':
                    boleto = Boleto(move_line)
                    if boleto:
                        self.write(cr, uid, move_line.id, {'date_payment_create': date.today()})
                    boletoList.append(boleto.boleto)
            except:
                continue
        return boletoList