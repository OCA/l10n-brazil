# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.one
    @api.depends('order_line.price_unit', 'order_line.product_qty',
                 'order_line.taxes_id')
    def _compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0
        amount_total = 0.0

        for line in self.order_line:
            taxes = line.taxes_id.compute_all(line.price_unit, line.product_qty,
            product=line.product_id, partner=self.partner_id,
            fiscal_position=self.fiscal_position)

            amount_untaxed += line.price_subtotal

            for tax in taxes['taxes']:
                tax_brw = self.env['account.tax'].browse(tax['id'])
                if not tax_brw.tax_code_id.tax_discount:
                    amount_tax += tax.get('amount', 0.0)

        self.amount_untaxed = self.pricelist_id.currency_id.round(amount_untaxed)
        self.amount_tax = self.pricelist_id.currency_id.round(amount_tax)
        self.amount_total = self.pricelist_id.currency_id.round(
            amount_untaxed + amount_tax)

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.purchase_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        default=_default_fiscal_category,
        domain="""[('type', '=', 'input'), ('state', '=', 'approved'),
            ('journal_type', '=', 'purchase')]""")
    amount_untaxed = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Untaxed Amount', store=True, help="The amount without tax")
    amount_tax = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Taxes', store=True, help="The tax amount")
    amount_total = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Total', store=True, help="The total amount")

    @api.multi
    def _fiscal_position_map(self, result, **kwargs):
        """Método para chamar a definição de regras fiscais"""
        ctx = dict(self._context)
        kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')

        ctx.update({'use_domain': ('use_purchase', '=', True)})
        return self.env[
            'account.fiscal.position.rule'].with_context(
                ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def onchange_fiscal_category_id(self, fiscal_category_id, partner_id,
                                    dest_address_id, company_id):

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        kwargs = {
            'company_id': company_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_id,
            'fiscal_category_id': fiscal_category_id,
            'partner_shipping_id': dest_address_id,
        }
        return self._fiscal_position_map(result, **kwargs)

    #TODO migrate to new API
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):

        result = super(PurchaseOrder, self)._prepare_inv_line(
            cr, uid, account_id, order_line, context)

        order = order_line.order_id

        result['fiscal_category_id'] = order_line.fiscal_category_id and \
        order_line.fiscal_category_id.id or order.fiscal_category_id and \
        order.fiscal_category_id.id

        result['fiscal_position'] = order_line.fiscal_position and \
        order_line.fiscal_position.id or order.fiscal_position and \
        order.fiscal_position.id

        result['cfop_id'] = order.fiscal_position and \
        order.fiscal_position.cfop_id and order.fiscal_position.cfop_id.id or \
        order.fiscal_position and order.fiscal_position.cfop_id and \
        order.fiscal_position.cfop_id.id

        result['partner_id'] = order_line.partner_id.id
        result['company_id'] = order_line.company_id.id

        return result

    #TODO migrate to new API
    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        result = super(PurchaseOrder, self)._prepare_invoice(
            cr, uid, order, line_ids, context)

        company_id = order.company_id
        if not company_id.document_serie_product_ids:
            raise except_orm(
                _('No fiscal document serie found!'),
                _("No fiscal document serie found for selected \
                company %s") % (order.company_id.name))

        journal_id = order.fiscal_category_id.property_journal.id
        if not journal_id:
            raise except_orm(
                _(u'Nenhuma Diário!'),
                _(u"Categoria de operação fisca: '%s', não tem um \
                diário contábil para a empresa %s") % (
                order.fiscal_category_id.name,
                order.company_id.name))

        #FIXME Se vazio deve ficar em branco
        comment = ''
        if order.fiscal_position.inv_copy_note and order.fiscal_position.note:
            comment = order.fiscal_position.note
        if order.notes:
            comment += ' - ' + order.notes

        result['issuer'] = '1'
        result['comment'] = comment,
        result['journal_id'] = journal_id
        result['fiscal_category_id'] = order.fiscal_category_id.id
        result['fiscal_position'] = order.fiscal_position.id

        return result

    #TODO migrate to new API
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id,
                                 group_id, context=None):
        result = super(PurchaseOrder, self)._prepare_order_line_move(
            cr, uid, order, order_line, picking_id, group_id, context)
        for move in result:
            move['fiscal_category_id'] = order_line.fiscal_category_id.id
            move['fiscal_position'] = order_line.fiscal_position.id
        return result


class PurchaseOrderLine(orm.Model):
    _inherit = 'purchase.order.line'
    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal',
            domain="[('type', '=', 'input'), \
            ('journal_type', '=', 'purchase')]"),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id', '=', fiscal_category_id)]")
    }

    def _fiscal_position_map(self, cr, uid, result, **kwargs):

        kwargs['context'].update({'use_domain': ('use_purchase', '=', True)})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        result_rule = fp_rule_obj.apply_fiscal_mapping(
            cr, uid, result, **kwargs)
        if kwargs.get('product_id', False) and \
        result_rule.get('fiscal_position', False):
            obj_fposition = self.pool.get('account.fiscal.position').browse(
                cr, uid, result_rule['fiscal_position'])
            obj_product = self.pool.get('product.product').browse(
                cr, uid, kwargs.get('product_id', False))
            kwargs['context'].update({'fiscal_type': obj_product.fiscal_type,
                            'type_tax_use': 'purchase'})
            taxes = obj_product.supplier_taxes_id or False
            tax_ids = self.pool.get('account.fiscal.position').map_tax(
                cr, uid, obj_fposition, taxes, kwargs.get('context'))

            result_rule['taxes_id'] = tax_ids

        return result_rule

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id,
                            qty, uom_id, partner_id, date_order=False,
                            fiscal_position_id=False, date_planned=False,
                            name=False, price_unit=False, context=None):
        if context is None:
            context = {}
        company_id = context.get('company_id')
        parent_fiscal_position_id = context.get('parent_fiscal_position_id')
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')

        result = {'value': {}}

        if product_id and parent_fiscal_category_id:
            obj_fp_rule = self.pool.get('account.fiscal.position.rule')
            product_fc_id = obj_fp_rule.product_fiscal_category_map(
                cr, uid, product_id, parent_fiscal_category_id)

            if product_fc_id:
                parent_fiscal_category_id = product_fc_id

            result['value']['fiscal_category_id'] = parent_fiscal_category_id

            kwargs = {
                'company_id': company_id,
                'product_id': product_id,
                'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'context': context,
            }
            result.update(self._fiscal_position_map(cr, uid, result, **kwargs))
            if result['value'].get('fiscal_position'):
                fiscal_position_id = result['value'].get('fiscal_position')

            obj_product = self.pool.get('product.product').browse(
                cr, uid, product_id)
            context.update({'fiscal_type': obj_product.fiscal_type,
                'type_tax_use': 'purchase'})

        result_super = super(PurchaseOrderLine, self).onchange_product_id(
            cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order, fiscal_position_id, date_planned, name, price_unit,
            context)
        result_super['value'].update(result['value'])
        return result_super

    def onchange_fiscal_category_id(self, cr, uid, ids, partner_id,
                                    dest_address_id=False,
                                    product_id=False,
                                    fiscal_category_id=False,
                                    company_id=False, context=None,
                                    **kwargs):
        result = {'value': {}}
        if not company_id or not partner_id:
            return result

        kwargs.update({
            'company_id': company_id,
            'product_id': product_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_id,
            'fiscal_category_id': fiscal_category_id,
            'context': context,
        })
        return self._fiscal_position_map(cr, uid, result, **kwargs)

    def onchange_fiscal_position(self, cr, uid, ids, partner_id,
                                 dest_address_id=False, product_id=False,
                                 fiscal_position=False,
                                 fiscal_category_id=False, company_id=False,
                                 context=None, **kwargs):
        result = {'value': {'taxes_id': False}}
        if not company_id or not partner_id:
            return result

        kwargs.update({
            'company_id': company_id,
            'product_id': product_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_id,
            'fiscal_category_id': fiscal_category_id,
            'context': context,
        })

        result.update(self._fiscal_position_map(cr, uid, result, **kwargs))
        fiscal_position = result['value'].get('fiscal_position')

        if product_id and fiscal_position:
            obj_fposition = self.pool.get('account.fiscal.position').browse(
                cr, uid, fiscal_position)
            obj_product = self.pool.get('product.product').browse(
                cr, uid, product_id)
            context = {'fiscal_type': obj_product.fiscal_type,
                       'type_tax_use': 'purchase'}
            taxes = obj_product.supplier_taxes_id or False
            taxes_ids = self.pool.get('account.fiscal.position').map_tax(
                cr, uid, obj_fposition, taxes, context)

            result['value']['taxes_id'] = taxes_ids

        return result
