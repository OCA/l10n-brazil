# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
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


from openerp import models, api


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)
        if payment_order.mode.type.code == '240':
            if payment_order.mode.payment_order_type == 'cobranca':
                domain += [
                    ('debit', '>', 0)
                ]
            # TODO: Refactory this
            index = domain.index(('invoice.payment_mode_id', '=', False))
            del domain[index - 1]
            domain.remove(('invoice.payment_mode_id', '=', False))
            index = domain.index(('date_maturity', '<=', self.duedate))
            del domain[index - 1]
            domain.remove(('date_maturity', '=', False))
            domain.remove(('date_maturity', '<=', self.duedate))
        return True
