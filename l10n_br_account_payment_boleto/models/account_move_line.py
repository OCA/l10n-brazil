# -*- coding: utf-8 -*-
#    Copyright (C) 2012-TODAY KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import date

from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)
    boleto_own_number = fields.Char(
        u'Nosso Número', readonly=True)

    @api.multi
    def send_payment(self):

        for move_line in self:

            if move_line.payment_mode_id.type_payment == '00':
                number_type = move_line.company_id.own_number_type
                if not move_line.boleto_own_number:
                    if number_type == '0':
                        nosso_numero = self.env['ir.sequence'].next_by_id(
                            move_line.company_id.own_number_sequence.id)
                    elif number_type == '1':
                        nosso_numero = \
                            move_line.transaction_ref.replace('/', '')
                    else:
                        nosso_numero = self.env['ir.sequence'].next_by_id(
                            move_line.payment_mode_id.
                            internal_sequence_id.id)
                else:
                    nosso_numero = move_line.boleto_own_number

                move_line.date_payment_created = date.today()
                # TODO - move_line.transaction_ref = \
                #    boleto.boleto.format_nosso_numero()
                move_line.boleto_own_number = nosso_numero

        return True
