# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
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


class SaleShop(orm.Model):
    _inherit = 'sale.shop'
    _columns = {
        'default_fc_id': fields.many2one(
            'l10n_br_account.fiscal.category', u'Categoria Fiscal Padrão')
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
        value = 0.0
        for c in self.pool.get('account.tax').compute_all(
            cr, uid, line.tax_id,
            line.price_unit * (1 - (line.discount or 0.0) / 100.0),
            line.product_uom_qty, line.order_id.partner_invoice_id.id,
            line.product_id, line.order_id.partner_id,
            fiscal_position=line.fiscal_position)['taxes']:
            tax = self.pool.get('account.tax').browse(cr, uid, c['id'])
            if not tax.tax_code_id.tax_discount:
                value += c.get('amount', 0.0)
        return value

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        result = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                result[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel') and \
                invoice.fiscal_category_id.id == sale.fiscal_category_id.id:
                    tot += invoice.amount_untaxed
            if tot:
                result[sale.id] = min(100.0, tot * 100.0 / (
                    sale.amount_untaxed or 1.00))
            else:
                result[sale.id] = 0.0
        return result

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="""[('type', '=', 'output'), ('journal_type', '=', 'sale'),
            ('state', '=', 'approved')]""",
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position',
            domain="[('fiscal_category_id', '=', fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'invoiced_rate': fields.function(
            _invoiced_rate, method=True, string='Invoiced', type='float'),
        'copy_note': fields.boolean(
            u'Copiar Observação no documentos fiscal'),
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
                    'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, string='Total',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty'], 10),
            },
              multi='sums', help="The total amount."),
        'amount_extra': fields.function(_amount_all, string='Extra',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty'], 10),
            },
              multi='sums', help="The total amount."),
        'amount_discount': fields.function(_amount_all, string='Desconto (-)',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty'], 10),
            },
              multi='sums', help="The discount amount."),
        'amount_gross': fields.function(_amount_all, string='Vlr. Bruto',
            digits_compute=dp.get_precision('Account'),
            store={
                'sale.order': (lambda self, cr, uid, ids,
                    c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id',
                    'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The discount amount."),
            'discount_rate': fields.float('Desconto', readonly=True,
            states={'draft': [('readonly', False)]}),
    }

    def _default_fiscal_category(self, cr, uid, context=None):
        result = False
        shop_id = context.get("shop_id", self.default_get(
            cr, uid, ["shop_id"], context)["shop_id"])
        if shop_id:
            shop = self.pool.get("sale.shop").read(
                cr, uid, [shop_id], ["default_fc_id"])
            if shop[0]["default_fc_id"]:
                result = shop[0]["default_fc_id"][0]
        return result

    _defaults = {
        'fiscal_category_id': _default_fiscal_category,
    }

    def onchange_discount_rate(self, cr, uid, ids, discount_rate):
        res = {}
        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=None):
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'discount': discount_rate}, context=None)
        return res

    def onchange_address_id(self, cr, uid, ids, partner_invoice_id,
                            partner_shipping_id, partner_id,
                            shop_id=None, context=None, **kwargs):
        if not context:
            context = {}
        fiscal_category_id=context.get('fiscal_category_id')
        return super(SaleOrder, self).onchange_address_id(
            cr, uid, ids, partner_invoice_id, partner_shipping_id,
            partner_id, shop_id, context,
            fiscal_category_id=fiscal_category_id)

    def onchange_shop_id(self, cr, uid, ids, shop_id=None, context=None,
                         partner_id=None, partner_invoice_id=None,
                         partner_shipping_id=None, **kwargs):
        if not context:
            context = {}
        fiscal_category_id=context.get('fiscal_category_id')
        return super(SaleOrder, self).onchange_shop_id(
            cr, uid, ids, shop_id, context, partner_id, partner_invoice_id,
            partner_shipping_id, fiscal_category_id=fiscal_category_id)

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                    partner_invoice_id=False, shop_id=False,
                                    fiscal_category_id=False, context=None):

        result = {'value': {'fiscal_position': False}}

        if not shop_id or not partner_id or not fiscal_category_id:
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_id = obj_shop.company_id.id
        context.update({'use_domain': ('use_sale', '=', True)})
        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'fiscal_category_id': fiscal_category_id,
            'company_id': company_id,
            'context': context
        }
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, **kwargs)

    def _fiscal_comment(self, cr, uid, order, context=None):
        fp_comment = []
        fp_ids = []

        for line in order.order_line:
            if line.fiscal_position and \
            line.fiscal_position.inv_copy_note and \
            line.fiscal_position.note:
                if not line.fiscal_position.id in fp_ids:
                    fp_comment.append(line.fiscal_position.note)
                    fp_ids.append(line.fiscal_position.id)

        return fp_comment

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

        inv_lines = self.pool.get('account.invoice.line').read(
            cr, uid, lines, ['fiscal_category_id', 'fiscal_position'])

        if (context.get('fiscal_type') == 'service' and
            inv_lines and inv_lines[0]['fiscal_category_id']):
                fiscal_category_id = inv_lines[0]['fiscal_category_id'][0]
                result['fiscal_position'] = inv_lines[0]['fiscal_position'][0]
        else:
            fiscal_category_id = order.fiscal_category_id.id

        if fiscal_category_id:
            journal = self.pool.get('l10n_br_account.fiscal.category').read(
                cr, uid, fiscal_category_id,
                ['property_journal'])['property_journal']
            if journal:
                result['journal_id'] = journal[0]

        result['partner_shipping_id'] = order.partner_shipping_id and \
        order.partner_shipping_id.id or False

        comment = []
        if order.note and order.copy_note:
            comment.append(order.note)

        fiscal_comment = self._fiscal_comment(cr, uid, order, context=context)
        result['comment'] = " - ".join(comment)
        result['fiscal_comment'] = " - ".join(fiscal_comment)
        result['fiscal_category_id'] = fiscal_category_id

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
                fiscal_position=line.fiscal_position)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_gross'] = line.price_unit * line.product_uom_qty
            res[line.id]['discount_value'] = res[line.id]['price_gross']-(price * line.product_uom_qty)
        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
            readonly=True, states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position',
            domain="[('fiscal_category_id','=',fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]}),
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

    def _fiscal_position_map(self, cr, uid, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_sale', '=', True)})
        obj_shop = self.pool.get('sale.shop').browse(
            cr, uid, kwargs.get('shop_id'))
        company_id = obj_shop.company_id.id
        kwargs.update({'company_id': company_id})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, **kwargs)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        if not context:
            context = {}
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        shop_id = context.get('shop_id')
        partner_invoice_id = context.get('partner_invoice_id')
        result = {'value': {}}
        if parent_fiscal_category_id and product and partner_invoice_id \
        and shop_id:
            obj_fp_rule = self.pool.get('account.fiscal.position.rule')
            product_fc_id = obj_fp_rule.product_fiscal_category_map(
                cr, uid, product, parent_fiscal_category_id)

            if product_fc_id:
                parent_fiscal_category_id = product_fc_id

            result['value']['fiscal_category_id'] = parent_fiscal_category_id

            kwargs = {
                'shop_id': shop_id,
                'partner_id': partner_id,
                'partner_invoice_id': partner_invoice_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'context': context
            }
            result.update(self._fiscal_position_map(cr, uid, result, **kwargs))
            if result['value'].get('fiscal_position'):
                fiscal_position = result['value'].get('fiscal_position')

            obj_product = self.pool.get('product.product').browse(
                cr, uid, product)
            context.update({'fiscal_type': obj_product.fiscal_type,
                'type_tax_use': 'sale'})

        result_super = super(SaleOrderLine, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)
        result_super['value'].update(result['value'])
        return result_super

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                        partner_invoice_id=False,
                                        shop_id=False, product_id=False,
                                        fiscal_category_id=False,
                                        context=None):

        if not context:
            context = {}
        result = {'value': {}}

        if not shop_id or not partner_id or not fiscal_category_id:
            return result

        kwargs = {
            'shop_id': shop_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'fiscal_category_id': fiscal_category_id,
            'context': context
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)

    def onchange_fiscal_position(self, cr, uid, ids, partner_id,
                                 partner_invoice_id=False, shop_id=False,
                                 product_id=False, fiscal_position=False,
                                 fiscal_category_id=False):
        result = {'value': {'tax_id': False}}
        if not shop_id or not partner_id:
            return result

        kwargs = {
            'shop_id': shop_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'fiscal_category_id': fiscal_category_id,
            'context': {}
        }
        result.update(self._fiscal_position_map(cr, uid, result, **kwargs))
        fiscal_position = result['value'].get('fiscal_position')

        if product_id and fiscal_position:
            obj_fposition = self.pool.get('account.fiscal.position').browse(
                cr, uid, fiscal_position)
            obj_product = self.pool.get('product.product').browse(
                cr, uid, product_id)
            context = {'fiscal_type': obj_product.fiscal_type,
                       'type_tax_use': 'sale'}
            taxes = obj_product.taxes_id or False
            tax_ids = self.pool.get('account.fiscal.position').map_tax(
                cr, uid, obj_fposition, taxes, context)

            result['value']['tax_id'] = tax_ids

        return result

    def _prepare_order_line_invoice_line(self, cr, uid, line,
                                         account_id=False, context=None):

        result = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id, context)

        result = self.l10n_br_sale_prepare_order_line_invoice_line(
            cr, uid, line, result, account_id, context)

        return result

    def l10n_br_sale_prepare_order_line_invoice_line(self, cr, uid, line, result,
                                         account_id=False, context=None):

        fc_id = line.fiscal_category_id or \
                line.order_id.fiscal_category_id or False

        if fc_id:
            result['fiscal_category_id'] = fc_id.id

        fp_id = line.fiscal_position or line.order_id.fiscal_position or False

        if fp_id:
            result['fiscal_position'] = fp_id.id

        return result
