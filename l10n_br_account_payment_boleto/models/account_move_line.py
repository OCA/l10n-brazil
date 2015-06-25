# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
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

from openerp import models, fields, api
from datetime import date
from ..boleto.document import Boleto

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_payment_created = fields.Date(
            u'Data da criação do pagamento', readonly=True)

    @api.multi
    def send_payment(self):
        boletoList = []

        for move_line in self:
            try:
                if move_line.payment_mode_id.type_payment == '00':
                    boleto = Boleto(move_line)
                    if boleto:
                        move_line.date_payment_created = date.today()
                    boletoList.append(boleto.boleto)
            except:
                continue
        return boletoList