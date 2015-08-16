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

import logging
from openerp import models, fields, api
from datetime import date
from ..boleto.document import Boleto
from ..boleto.document import BoletoException

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)

    @api.multi
    def send_payment(self):
        boleto_list = []

        for move_line in self:
            try:

                if move_line.payment_mode_id.type_payment == '00':
                    number_type = move_line.company_id.own_number_type
                    if not move_line.boleto_own_number:
                        if number_type == '0':                            
                            nosso_numero = self.env['ir.sequence'].next_by_id(
                                move_line.company_id.own_number_sequence.id)
                        elif number_type == '1':
                            nosso_numero = move_line.transaction_ref
                        else:
                            nosso_numero = self.env['ir.sequence'].next_by_id(
                                move_line.payment_mode_id.internal_sequence_id.id)
                    else:
                        nosso_numero = move_line.boleto_own_number

                    boleto = Boleto.getBoleto(move_line, nosso_numero)
                    if boleto:
                        move_line.date_payment_created = date.today()
                        move_line.transaction_ref = \
                            boleto.boleto.format_nosso_numero()
                        move_line.boleto_own_number = nosso_numero

                    boleto_list.append(boleto.boleto)
            except BoletoException as be:
                _logger.error(be.message or be.value, exc_info=True)
                continue
            except Exception as e:
                _logger.error(e.message or e.value, exc_info=True)
                continue
        return boleto_list
