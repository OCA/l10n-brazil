# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Daniel Sadamo <sadamo@kmee.com.br>
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


def calc_price_ratio(price_gross, amount_calc, amount_total):
    return price_gross * amount_calc / amount_total


class l10n_brAccountInvoiceCostsRatio(orm.TransientModel):
    _name = 'l10n_br_account_product.invoice.costs_ratio'

    _columns = {
        'amount_freight_value': fields.float('Frete'),
        'amount_insurance_value': fields.float('Seguro'),
        'amount_costs_value': fields.float('Outros Custos'),
    }

    def values_set(self, cr, uid, ids, context=None):

        invoice_pool = self.pool.get('account.invoice')
        invoice_line_pool = self.pool.get('account.invoice.line')
        delivery = self.browse(cr, uid, ids[0], context)

        if context.get('active_id', False):
            invoice_data = invoice_pool.read(cr, uid, context.get('active_id'),
                                             ['invoice_line', 'amount_gross'])

        invoice_pool.write(cr, uid, invoice_data['id'], {
            'amount_freight': delivery.amount_freight_value,
            'amount_insurance': delivery.amount_insurance_value,
            'amount_costs': delivery.amount_costs_value,
        }, context=context)

        for line_id in invoice_data['invoice_line']:
            line = invoice_line_pool.browse(cr, uid, line_id, context)
            invoice_line_pool.write(cr, uid, line_id,
                                    {'freight_value': calc_price_ratio(
                                        line.price_gross,
                                        delivery.amount_freight_value,
                                        invoice_data['amount_gross']),
                                     'insurance_value': calc_price_ratio(
                                         line.price_gross,
                                         delivery.amount_insurance_value,
                                         invoice_data['amount_gross']),
                                     'other_costs_value': calc_price_ratio(
                                         line.price_gross,
                                         delivery.amount_costs_value,
                                         invoice_data['amount_gross']),
                                     },
                                    context=context)

        return True
