# -*- coding: utf-8 -*-
# #############################################################################
#
#
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Fernando Marcato Rodrigues
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
    _inherit = "payment.mode"

    # FIXME: não consegui adicionar o item de selection.
    # Consegui mudar a string do campo, mas o selection não.
    payment_order_type = fields.Selection(string="Order Type",
        selection=[
            ('payment', 'Payment'), ('debit', 'Debit'),
            ('cobranca240', u'Cobrança CNAB 240')],
        help="This field, that comes from export type, determines if this "
             "mode can be selected for customers or suppliers.")

    # A exportação CNAB não se encaixa somente nos parâmetros de
    # débito e crédito.
