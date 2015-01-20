# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm, fields
from openerp.addons import decimal_precision as dp


def  calc_price_ratio(price_gross, amount_calc, amount_total):
    return price_gross * amount_calc / amount_total

class SaleShop(orm.Model):
    _inherit = 'sale.shop'

    _columns = {
        'default_ind_pres': fields.selection([
            ('0', u'Não se aplica'),
            ('1', u'Operação presencial'),
            ('2', u'Operação não presencial, pela Internet'),
            ('3', u'Operação não presencial, Teleatendimento'),
            ('4', u'NFC-e em operação com entrega em domicílio'),
            ('9', u'Operação não presencial, outros'),
        ], u'Tipo de operação',
            help=u'Indicador de presença do comprador no \
                \nestabelecimento comercial no momento \
                \nda operação.'),
    }

class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        result = {}
        for order in self.browse(cr, uid, ids, context=context):
            result[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_extra': 0.0,
                'amount_discount': 0.0,
                'amount_gross': 0.0,
            }
            val = val1 = val2 = val3 = val4 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
                val2 += (line.insurance_value + line.freight_value + line.other_costs_value)
                val3 += line.discount_value
                val4 += line.price_gross
            result[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            result[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            result[order.id]['amount_extra'] = cur_obj.round(cr, uid, cur, val2)
            result[order.id]['amount_total'] = result[order.id]['amount_untaxed'] + result[order.id]['amount_tax'] + result[order.id]['amount_extra']
            result[order.id]['amount_discount'] = cur_obj.round(cr, uid, cur, val3)
            result[order.id]['amount_gross'] = cur_obj.round(cr, uid, cur, val4)
        return result

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(
            cr, uid, line.tax_id,
            line.price_unit * (1 - (line.discount or 0.0) / 100.0),
            line.product_uom_qty, line.order_id.partner_invoice_id.id,
            line.product_id, line.order_id.partner_id,
            fiscal_position=line.fiscal_position,
            insurance_value=line.insurance_value,
            freight_value=line.freight_value,
            other_costs_value=line.other_costs_value)['taxes']:
            tax = self.pool.get('account.tax').browse(cr, uid, c['id'])
            if not tax.tax_code_id.tax_discount:
                val += c.get('amount', 0.0)
        return val

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(
            cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'amount_untaxed': fields.function(_amount_all, string='Untaxed Amount',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.",
            track_visibility='always'),
        'amount_tax': fields.function(_amount_all, string='Taxes',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty', 'freight_value',
                    'insurance_value', 'other_costs_value'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, string='Total',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty', 'freight_value',
                    'insurance_value', 'other_costs_value'], 10),
            },
              multi='sums', help="The total amount."),
        'amount_extra': fields.function(_amount_all, string='Extra',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty', 'freight_value',
                    'insurance_value', 'other_costs_value'], 10),
            },
              multi='sums', help="The total amount."),
        'amount_discount': fields.function(_amount_all, string='Desconto (-)',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty', 'freight_value',
                    'insurance_value', 'other_costs_value'], 10),
            },
              multi='sums', help="The discount amount."),
        'amount_gross': fields.function(_amount_all, string='Vlr. Bruto',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty', 'freight_value',
                    'insurance_value', 'other_costs_value'], 10),
            },
              multi='sums', help="The discount amount."),
        'amount_freight': fields.float('Frete',
             digits_compute=dp.get_precision('Account'), readonly=True,
                               states={'draft': [('readonly', False)]}),
        'amount_costs': fields.float('Outros Custos',
            digits_compute=dp.get_precision('Account'), readonly=True,
                               states={'draft': [('readonly', False)]}),
        'amount_insurance': fields.float('Seguro',
            digits_compute=dp.get_precision('Account'), readonly=True,
                               states={'draft': [('readonly', False)]}),
        'discount_rate': fields.float('Desconto', readonly=True,
                               states={'draft': [('readonly', False)]}),
        'ind_pres': fields.selection([
            ('0', u'Não se aplica'),
            ('1', u'Operação presencial'),
            ('2', u'Operação não presencial, pela Internet'),
            ('3', u'Operação não presencial, Teleatendimento'),
            ('4', u'NFC-e em operação com entrega em domicílio'),
            ('9', u'Operação não presencial, outros'),
        ], u'Tipo de operação', readonly=True,
            states={'draft': [('readonly', False)]}, required=False,
            help=u'Indicador de presença do comprador no \
                \nestabelecimento comercial no momento \
                \nda operação.'),
    }

    def _default_ind_pres(self, cr, uid, context=None):
        result = False
        shop_id = context.get("shop_id", self.default_get(
            cr, uid, ["shop_id"], context)["shop_id"])
        if shop_id:
            shop = self.pool.get("sale.shop").read(
                cr, uid, [shop_id], ["default_ind_pres"])
            if shop[0]["default_ind_pres"]:
                result = shop[0]["default_ind_pres"][0]
        return result

    _defaults = {
        'amount_freight': 0.00,
        'amount_costs': 0.00,
        'amount_insurance': 0.00,
        'ind_pres': _default_ind_pres,
    }

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        result = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context)

        if order.ind_pres:
            result['ind_pres'] = order.ind_pres

        return result

    def _fiscal_comment(self, cr, uid, order, context=None):
        fp_comment = []
        fc_comment = []
        fc_ids = []

        fp_comment = super(SaleOrder, self)._fiscal_comment(
            cr, uid, order, context)

        for line in order.order_line:
            if line.product_id.ncm_id:
                fc = line.product_id.ncm_id
                if fc.inv_copy_note and fc.note:
                    if not fc.id in fc_ids:
                        fc_comment.append(fc.note)
                        fc_ids.append(fc.id)

        return fp_comment + fc_comment

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None,
                            date_invoice=False, context=None):
        invoice_id = super(SaleOrder, self).action_invoice_create(
            cr, uid, ids, grouped, states, date_invoice, context)

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)

        inv = self.pool.get("account.invoice").browse(
            cr, uid, invoice_id, context=context)
        vals = [
            ('Frete', company.account_freight_id, inv.amount_freight),
            ('Seguro', company.account_insurance_id, inv.amount_insurance),
            ('Outros Custos', company.account_other_costs, inv.amount_costs)
        ]

        ait_obj = self.pool.get('account.invoice.tax')
        for tax in vals:
            if tax[2] > 0:
                ait_obj.create(cr, uid,
                {
                 'invoice_id': invoice_id,
                 'name': tax[0],
                 'account_id': tax[1].id,
                 'amount': tax[2],
                 'base': tax[2],
                 'manual': 1,
                 'company_id': company.id,
                }, context=context)
        return invoice_id

    def onchange_amount_freight(self, cr, uid, ids, amount_freight=False):
        result = {}
        if (amount_freight is False) or not ids:
            return {'value': {'amount_freight': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'freight_value':
            calc_price_ratio(line.price_gross, amount_freight,
                order.amount_gross)}, context=None)
        return result

    def onchange_amount_insurance(self, cr, uid, ids, amount_insurance=False):
        result = {}
        if (amount_insurance is False) or not ids:
            return {'value': {'amount_insurance': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'insurance_value':
          calc_price_ratio(line.price_gross, amount_insurance,
                order.amount_gross)}, context=None)
        return result

    def onchange_amount_costs(self, cr, uid, ids, amount_costs=False):
        result = {}
        if (amount_costs is False) or not ids:
            return {'value': {'amount_costs': 0.00}}

        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'other_costs_value':
          calc_price_ratio(line.price_gross, amount_costs,
                order.amount_gross)}, context=None)
        return result


class SaleOrderLine(orm.Model):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}

        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'price_subtotal': 0.0,
                'price_gross': 0.0,
                'discount_value': 0.0,
            }
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price,
                line.product_uom_qty, line.order_id.partner_invoice_id.id,
                line.product_id, line.order_id.partner_id,
                fiscal_position=line.fiscal_position,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_gross'] = line.price_unit * line.product_uom_qty
            res[line.id]['discount_value'] = res[line.id]['price_gross']-(price * line.product_uom_qty)
        return res

    _columns = {
        'insurance_value': fields.float('Insurance',
             digits_compute=dp.get_precision('Account')),
        'other_costs_value': fields.float('Other costs',
             digits_compute=dp.get_precision('Account')),
        'freight_value': fields.float('Freight',
             digits_compute=dp.get_precision('Account')),
         'discount_value': fields.function(
             _amount_line, string='Vlr. Desc. (-)',
             digits_compute=dp.get_precision('Sale Price'), multi='sums'),
        'price_gross': fields.function(
            _amount_line, string='Vlr. Bruto',
            digits_compute=dp.get_precision('Sale Price'), multi='sums'),
        'price_subtotal': fields.function(
            _amount_line, string='Subtotal',
            digits_compute=dp.get_precision('Sale Price'), multi='sums'),
    }
    _defaults = {
        'insurance_value': 0.00,
        'other_costs_value': 0.00,
        'freight_value': 0.00,
    }

    def _prepare_order_line_invoice_line(self, cr, uid, line,
                                         account_id=False, context=None):

        result = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id, context)

        result['insurance_value'] = line.insurance_value
        result['other_costs_value'] = line.other_costs_value
        result['freight_value'] = line.freight_value

        #FIXME
        # Necessário informar estes campos pois são related do
        # objeto account.invoice e quando o método create do
        # account.invoice.line é invocado os valores são None
        result['company_id'] = line.order_id.company_id.id
        result['partner_id'] = line.order_id.partner_id.id

        result = self.l10n_br_sale_product_prepare_order_line_invoice_line(
            cr, uid, line, result, account_id, context)

        return result

    def l10n_br_sale_product_prepare_order_line_invoice_line(self, cr, uid, line,
                                                              result, account_id=False, context=None):

        if line.product_id.fiscal_type == 'product':
            if line.fiscal_position:
                cfop = self.pool.get("account.fiscal.position").read(
                    cr, uid, [line.fiscal_position.id], ['cfop_id'],
                    context=context)
                if cfop[0]['cfop_id']:
                    result['cfop_id'] = cfop[0]['cfop_id'][0]

        return result