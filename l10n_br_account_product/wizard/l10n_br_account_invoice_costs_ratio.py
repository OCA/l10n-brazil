# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Daniel Sadamo <sadamo@kmee.com.br>
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
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


class L10nBrAccountProductInvoiceCostsRatio(orm.TransientModel):

    _name = 'l10n_br_account_product.invoice.costs_ratio'

    _columns = {
        'amount_freight_value': fields.float('Frete'),
        'amount_insurance_value': fields.float('Seguro'),
        'amount_costs_value': fields.float('Outros Custos'),
    }

    def values_set(self, cr, uid, ids, context=None):

        if not (context.get('active_model')
                in ('account.invoice')):
            return False

        def calc_price_ratio(price_gross, amount_calc, amount_total):
            if ammount_total:
                return price_gross * amount_calc / amount_total
            else:
                return 0.0

        for delivery in self.browse(cr, uid, ids, context):
            for invoice in self.pool.get('account.invoice').browse(
                    cr, uid, context.get('active_ids', [])):
                for line in invoice.invoice_line:
                    vals = {
                        'freight_value': calc_price_ratio(
                            line.price_gross, delivery.amount_freight_value,
                            invoice.amount_gross),
                        'insurance_value': calc_price_ratio(
                            line.price_gross, delivery.amount_insurance_value,
                            invoice.amount_gross),
                        'other_costs_value': calc_price_ratio(
                            line.price_gross, delivery.amount_costs_value,
                            invoice.amount_gross),
                        }
                    print line
                    print vals
                    self.pool.get('account.invoice.line').write(
                        cr, uid, [line.id], vals, context)
        return True
