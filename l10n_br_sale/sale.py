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

import decimal_precision as dp
from osv import fields, osv
from tools.translate import _


class sale_shop(osv.osv):
    _inherit = 'sale.shop'
    _columns = {
                'default_fc_id': fields.many2one(
                    'l10n_br_account.fiscal.category',
                    'Categoria Fiscal Padrão')}

sale_shop()


class sale_order(osv.osv):
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
                if invoice.state not in ('draft', 'cancel') and invoice.fiscal_category_id.id == sale.fiscal_category_id.id:
                    tot += invoice.amount_untaxed
            if tot:
                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_untaxed or 1.00))
            else:
                res[sale.id] = 0.0
        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria',
            domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', 'Fiscal Position',
            domain="[(fiscal_category_id', '=', fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'invoiced_rate': fields.function(_invoiced_rate, method=True,
                                         string='Invoiced', type='float')}

    def onchange_partner_id(self, cr, uid, ids, partner_id=False,
                            partner_invoice_id=False, shop_id=False,
                            fiscal_category_id=False):

        result = super(sale_order, self).onchange_partner_id(cr, uid, ids,
                                                             partner_id)

        if not shop_id or not partner_id:
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_id = obj_shop.company_id.id

        if not fiscal_category_id:
            fiscal_category_id = obj_shop.default_fc_id.id
        
        result['value']['fiscal_category_id'] = fiscal_category_id

        partner_invoice_id = result['value'].get('partner_invoice_id', False)
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        fiscal_result = obj_fp_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id,
            context={'use_domain': ('use_sale', '=',True)})

        result['value'].update(fiscal_result)

        return result

    def onchange_partner_invoice_id(self, cr, uid, ids,
                                    partner_invoice_id=False, partner_id=False,
                                    shop_id=False, fiscal_category_id=False):

        result = {'value': {}}

        if not shop_id or not partner_id:
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_id = obj_shop.company_id.id

        if not fiscal_category_id:
            fiscal_category_id = obj_shop.default_fc_id.id
        
        result['fiscal_operation_category_id'] = fiscal_category_id

        result = super(sale_order, self).onchange_partner_invoice_id(cr, uid, ids, partner_invoice_id, partner_id, shop_id)
        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        fiscal_result = obj_fp_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id,
            context={'use_domain': ('use_sale', '=', True)})

        result['value'].update(fiscal_result)

        return result

    def onchange_shop_id(self, cr, uid, ids, shop_id=False, partner_id=False,
                         partner_invoice_id=False, fiscal_category_id=False):

        result = super(sale_order, self).onchange_shop_id(
            cr, uid, ids, shop_id, partner_id, partner_invoice_id)

        if not shop_id:
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_id = obj_shop.company_id.id

        result['value']['fiscal_category_id'] = fiscal_category_id or \
        (obj_shop.default_fc_id and obj_shop.default_fc_id.id or False)

        if not partner_id:
            return result

        obj_fiscal_position_rule = self.pool.get('account.fiscal.position.rule')
        fiscal_result = obj_fiscal_position_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id,
            context={'use_domain': ('use_sale', '=', True)})

        result['value'].update(fiscal_result)

        return result

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                    partner_invoice_id=False, shop_id=False,
                                    fiscal_category_id=False):

        result = {'value': {'fiscal_operation_id': False,
                            'fiscal_position': False}}

        if not shop_id or not partner_id or not fiscal_category_id:
            return result

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        company_id = obj_shop.company_id.id

        result['value']['fiscal_category_id'] = fiscal_category_id or (obj_shop.default_fc_id and obj_shop.default_fc_id.id)

        obj_fp_rule = self.pool.get('account.fiscal.position.rule')

        fiscal_result = obj_fp_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, company_id,
            fiscal_category_id,
            context={'use_domain': ('use_sale', '=', True)})

        result['value'].update(fiscal_result)
        # FIXME - PQ Excluia a Categoria fiscal?????
        #del result['value']['fiscal_category_id']

        return result

    def _make_invoice(self, cr, uid, order, lines, context=None):
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        lines_service = []
        lines_product = []
        inv_ids = []
        inv_id_product = False
        inv_id_service = False

        if context is None:
            context = {}

        obj_company = self.pool.get('res.company').browse(cr, uid,
                                                          order.company_id.id)

        if not obj_company.product_invoice_id or \
        not obj_company.service_invoice_id:
            raise osv.except_osv(
                _('No fiscal document serie found !'),
                _("No fiscal document serie found for selected company %s") % (
                    order.company_id.name))

        if order.fiscal_category_id.property_journal:
            raise osv.except_osv(
                _('Error !'),
                _('There is no journal defined for this company in Fiscal \
                Category: %s Company: %s)') % (
                    order.fiscal_category_id.name, order.company_id.name))

        for inv_line in obj_invoice_line.browse(cr, uid, lines, context=context):
            if inv_line.product_id.fiscal_type == 'service' or inv_line.product_id.is_on_service_invoice:
                lines_service.append(inv_line.id)

            if inv_line.product_id.fiscal_type == 'product':
                lines_product.append(inv_line.id)

        if lines_service:
            inv_id_service = super(sale_order, self)._make_invoice(cr, uid, order, lines_service, context=None)
            inv_ids.append(inv_id_service)

        if lines_product:
            inv_id_product = super(sale_order, self)._make_invoice(cr, uid, order, lines_product, context=None)
            inv_ids.append(inv_id_product)

        for inv in inv_obj.browse(cr, uid, inv_ids, context=None):

            service_type_id = False
            comment = ''
            fiscal_type = ''
            fiscal_operation_category_id = order.fiscal_operation_category_id
            fiscal_operation_id = order.fiscal_operation_id
            fiscal_position = order.fiscal_position and order.fiscal_position.id

            inv_line_ids = map(lambda x: x.id, inv.invoice_line)

            order_lines = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoice_lines', 'in', inv_line_ids)], context=context)
            for order_line in self.pool.get('sale.order.line').browse(cr, uid, order_lines, context=context):
                inv_line_id = [inv_line for inv_line in order_line.invoice_lines if inv_line.id in inv_line_ids]
                if inv_line_id:
                    obj_invoice_line.write(
                        cr, uid, inv_line_id[0].id, {'fiscal_category_id': order_line.fiscal_category_id.id or order.fiscal_category_id.id,
                                                     'cfop_id': (order_line.fiscal_position and order_line.fiscal_position.cfop_id.id) or (order.fiscal_position and order.fiscal_position.cfop_id.id) or False})

                    if order_line.product_id.fiscal_type == 'service' or inv_line.product_id.is_on_service_invoice:
                        fiscal_operation_category_id = order_line.fiscal_operation_category_id or order.fiscal_operation_category_id or False
                        #Em quanto não tem as posições fiscais na linha coloca falso na nota de serviço
                        fiscal_position = order_line.fiscal_position
                        service_type_id = (order_line.fiscal_operation_id and order_line.fiscal_operation_id.service_type_id.id) or (order.fiscal_operation_id and order.fiscal_operation_id.service_type_id.id) or False
                        fiscal_type = order_line.product_id.fiscal_type

            if fiscal_operation_id or order.fiscal_operation_id.inv_copy_note:
                comment = fiscal_operation_id and fiscal_operation_id.note or ''

            if order.note:
                comment += ' - ' + order.note

            inv_l10n_br = {
               'fiscal_operation_category_id': fiscal_operation_category_id and fiscal_operation_category_id.id,
               # Agora o documento fiscal vem por padrão 
               #'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id,
               #'document_serie_id': fiscal_document_serie_ids[0].id,
               'service_type_id': service_type_id,
               'fiscal_type': fiscal_type or 'product',
               'fiscal_position': fiscal_position,
               'comment': comment,
               'journal_id': fiscal_category_id and fiscal_category_id.property_journal and fiscal_category_id.property_journal.id or False,
            }

            inv_obj.write(cr, uid, inv.id, inv_l10n_br, context=context)
            inv_obj.button_compute(cr, uid, [inv.id])
        return inv_id_product or inv_id_service

    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(sale_order, self)._prepare_order_picking(cr, uid, order, context)
        result['fiscal_category_id'] = order.fiscal_category_id and order.fiscal_category_id.id
        result['fiscal_position'] = order.fiscal_position and order.fiscal_position.id
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

sale_order()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}

        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id, fiscal_operation=line.fiscal_operation_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria',
            domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_position': fields.many2one(
            'account.fiscal.position','Fiscal Position',
            domain="[('fiscal_category_id','=',fiscal_category_id)]",
            readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(
            _amount_line, string='Subtotal',
            digits_compute=dp.get_precision('Sale Price'))}

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None,
                          fiscal_category_id=False, shop_id=False,
                          parent_fiscal_position=False,
                          partner_invoice_id=False):

        result = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)

        if not fiscal_category_id or not product or not partner_invoice_id:
            return result

        obj_fp_rule = self.pool.get('account.fiscal.position.rule')
        product_fiscal_category_id = obj_fp_rule.product_fiscal_category_map(
            cr, uid, product, fiscal_category_id)

        if not product_fiscal_category_id:
            result['value']['fiscal_category_id'] = fiscal_category_id
            return result

        result['value']['fiscal_category_id'] = product_fiscal_category_id

        obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
        fiscal_result = obj_fp_rule.fiscal_position_map(
            cr, uid, partner_id, partner_invoice_id, obj_shop.company_id.id,
            product_fiscal_category_id,
            context={'use_domain': ('use_sale', '=', True)})

        result['value'].update(fiscal_result)
        return result

    def create_sale_order_line_invoice(self, cr, uid, ids, context=None):
        
        result = super(sale_order_line, self).create_sale_order_line_invoice(
            cr, uid, ids, context)
        inv_ids = []
        if result:

            for so_line in self.browse(cr, uid, ids):
                for inv_line in so_line.invoice_lines:
                    if inv_line.invoice_id.state in ('draft'):
                        company_id = self.pool.get('res.company').browse(cr, uid, order.company_id.id)
                        if not company_id.document_serie_product_ids:
                            raise osv.except_osv(_('No fiscal document serie found !'), _("No fiscal document serie found for selected company %s and fiscal operation: '%s'") % (order.company_id.name, order.fiscal_operation_id.code))
                        if inv_line.invoice_id.id not in inv_ids:
                            inv_ids.append(inv_line.id)
                            self.pool.get('account.invoice').write(cr, uid, inv_line.invoice_id.id, {'fiscal_category_id': so_line.order_id.fiscal_category_id.id})
                                                                                                     # CHECK - Agora o documento fiscal e a série de documento fiscal e padrão na nota fiscal
                                                                                                     #'fiscal_document_id': so_line.order_id.fiscal_operation_id.fiscal_document_id.id,
                                                                                                     #'document_serie_id': company_id.document_serie_product_ids[0].id

                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': so_line.fiscal_position.cfop_id.id,
                                                                                           'fiscal_category_id': so_line.fiscal_category_id.id})

        return result

sale_order_line()
