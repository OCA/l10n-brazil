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
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp


class sale_shop(orm.Model):
    _inherit = 'sale.shop'
    _columns = {
        'default_fc_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal Padrão')
    }


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _get_order(self, cr, uid, ids, context={}):
        result = super(sale_order, self)._get_order(cr, uid, ids, context)
        return result.keys()

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel') and \
                invoice.fiscal_category_id.id == sale.fiscal_category_id.id:
                    tot += invoice.amount_untaxed
            if tot:
                res[sale.id] = min(100.0, tot * 100.0 / (
                    sale.amount_untaxed or 1.00))
            else:
                res[sale.id] = 0.0
        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position',
            domain="[('fiscal_category_id', '=', fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'invoiced_rate': fields.function(_invoiced_rate, method=True,
                                         string='Invoiced', type='float')
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

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        return super(sale_order, self).onchange_partner_id(
            cr, uid, ids, partner_id, context)

    def onchange_address_id(self, cr, uid, ids, partner_invoice_id,
                            partner_shipping_id, partner_id,
                            shop_id=None, context=None,
                            fiscal_category_id=None, **kwargs):
        return super(sale_order, self).onchange_address_id(
            cr, uid, ids, partner_invoice_id, partner_shipping_id,
            partner_id, shop_id, context,
            fiscal_category_id=fiscal_category_id)

    def onchange_shop_id(self, cr, uid, ids, shop_id=None, context=None,
                         partner_id=None, partner_invoice_id=None,
                         partner_shipping_id=None,
                         fiscal_category_id=None, **kwargs):
        return super(sale_order, self).onchange_shop_id(
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
            'company_id': company_id,
            'context': context
        }
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, kwargs)

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
        result = super(sale_order, self)._prepare_invoice(
            cr, uid, order, lines, context)

        obj_inv_lines = self.pool.get('account.invoice.line').read(
            cr, uid, lines, ['fiscal_category_id', 'fiscal_position'])

        if context.get('fiscal_type') == 'service':
            if obj_inv_lines:
                fiscal_category_id = obj_inv_lines[0]['fiscal_category_id'][0]
                result['fiscal_position'] = obj_inv_lines[0]['fiscal_position'][0]
                if fiscal_category_id:
                    journal = self.pool.get(
                        'l10n_br_account.fiscal.category').read(cr, uid,
                        fiscal_category_id,
                        ['property_journal'])['property_journal']
                    if journal:
                        result['journal_id'] = journal[0]
        else:
            fiscal_category_id = order.fiscal_category_id.id
            result['journal_id'] = order.fiscal_category_id.property_journal.id

        result['partner_shipping_id'] = order.partner_shipping_id and \
        order.partner_shipping_id.id or False

        fp_comment = []
        fc_comment = []
        fp_ids = []
        fc_ids = []
        if order.note:
            fp_comment.append(order.note)

        for line in order.order_line:
            if line.fiscal_position and \
            line.fiscal_position.inv_copy_note and \
            line.fiscal_position.note:
                if not line.lllfiscal_position.id in fp_ids:
                    fp_comment.append(line.fiscal_position.note)
                    fp_ids.append(line.fiscal_position.id)

            if line.product_id.property_fiscal_classification:
                fc = line.product_id.property_fiscal_classification
                if fc.inv_copy_note and fc.note:
                    if not fc.id in fc_ids:
                        fc_comment.append(fc.note)
                        fc_ids.append(fc.id)

        result['comment'] = " - ".join(fp_comment + fc_comment)
        result['fiscal_category_id'] = fiscal_category_id
        return result

    def _make_invoice(self, cr, uid, order, lines, context=None):
        obj_invoice_line = self.pool.get('account.invoice.line')
        lines_service = []
        lines_product = []
        inv_product_ids = []
        inv_service_ids = []
        inv_id_product = False
        inv_id_service = False

        if not context:
            context = {}

        obj_company = self.pool.get('res.company').browse(
            cr, uid, order.shop_id.company_id.id)

        if not obj_company.product_invoice_id or \
        not obj_company.service_invoice_id:
            raise orm.except_orm(
                _('No fiscal document serie found !'),
                _("No fiscal document serie found for selected company %s") % (
                    order.company_id.name))

        if not order.fiscal_category_id.property_journal:
            raise orm.except_orm(
                _('Error !'),
                _('There is no journal defined for this company in Fiscal \
                Category: %s Company: %s)') % (
                    order.fiscal_category_id.name, order.company_id.name))

        for inv_line in obj_invoice_line.browse(cr, uid, lines, context=context):
            if inv_line.product_id.fiscal_type == 'service' or inv_line.product_id.is_on_service_invoice:
                lines_service.append(inv_line.id)

            if inv_line.product_id.fiscal_type == 'product':
                lines_product.append(inv_line.id)

        if lines_product:
            context['fiscal_type'] = 'product'
            inv_id_product = super(sale_order, self)._make_invoice(
                cr, uid, order, lines_product, context=context)
            inv_product_ids.append(inv_id_product)

        if lines_service:
            context['fiscal_type'] = 'service'
            inv_id_service = super(sale_order, self)._make_invoice(
                cr, uid, order, lines_service, context=context)
            inv_service_ids.append(inv_id_service)

        return inv_id_product or inv_id_service

    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(sale_order, self)._prepare_order_picking(cr, uid,
            order, context)
        result['fiscal_category_id'] = order.fiscal_category_id and \
        order.fiscal_category_id.id
        result['fiscal_position'] = order.fiscal_position and \
        order.fiscal_position.id
        return result

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(
            cr, uid, line.tax_id,
            line.price_unit * (1 - (line.discount or 0.0) / 100.0),
            line.product_uom_qty, line.order_id.partner_invoice_id.id,
            line.product_id, line.order_id.partner_id,
            fiscal_position=line.fiscal_position)['taxes']:
            tax = self.pool.get('account.tax').browse(cr, uid, c['id'])
            if not tax.tax_code_id.tax_discount:
                val += c.get('amount', 0.0)
        return val


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}

        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price,
                line.product_uom_qty, line.order_id.partner_invoice_id.id,
                line.product_id, line.order_id.partner_id,
                fiscal_position=line.fiscal_position)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position',
            domain="[('fiscal_category_id','=',fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(
            _amount_line, string='Subtotal',
            digits_compute=dp.get_precision('Sale Price'))}

    def _fiscal_position_map(self, cr, uid, result, **kwargs):

        kwargs['context'].update({'use_domain': ('use_sale', '=', True)})
        obj_shop = self.pool.get('sale.shop').browse(
            cr, uid, kwargs.get('shop_id'))
        company_id = obj_shop.company_id.id
        kwargs.update({'company_id': company_id})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')

        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, kwargs)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None,
                          parent_fiscal_category_id=False, shop_id=False,
                          parent_fiscal_position=False,
                          partner_invoice_id=False, **kwargs):

        result = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)

        if not parent_fiscal_category_id or not product or not partner_invoice_id:
            return result

        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        product_fiscal_category_id = obj_fp_rule.product_fiscal_category_map(
            cr, uid, product, parent_fiscal_category_id)

        if product_fiscal_category_id:
            parent_fiscal_category_id = product_fiscal_category_id

        result['value']['fiscal_category_id'] = parent_fiscal_category_id

        kwargs = {
            'shop_id': shop_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'fiscal_category_id': parent_fiscal_category_id,
            'context': context
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)

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
        if not shop_id or not partner_id or not fiscal_position:
            return result

        if product_id:
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

        kwargs = {
            'shop_id': shop_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'fiscal_category_id': fiscal_category_id,
            'context': {}
        }
        return self._fiscal_position_map(cr, uid, result, **kwargs)

    def _prepare_order_line_invoice_line(self, cr, uid, line,
                                         account_id=False, context=None):
        result = super(sale_order_line, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id, context)

        fc_id = line.fiscal_category_id or \
        line.order_id.fiscal_category_id or False
        if fc_id:
            result['fiscal_category_id'] = fc_id.id

        fp = line.fiscal_position or line.order_id.fiscal_position or False
        if fp:
            result['fiscal_position'] = fp.id
            if line.product_id.fiscal_type == 'product':
                result['cfop_id'] = fp.cfop_id and fp.cfop_id.id or False

        result['partner_id'] = line.order_id.partner_id.id
        result['company_id'] = line.order_id.company_id.id
        return result
