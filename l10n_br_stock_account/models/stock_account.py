# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Renato Lima - Akretion
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _default_fiscal_category(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.stock_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, domain="[('state', '=', 'approved')]",
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    fiscal_position = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)]})

    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        if ctx.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({'use_domain': ('use_picking', '=', True)})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def onchange_fiscal_category_id(self, fiscal_category_id, partner_id,
                                    company_id):

        result = {'value': {'fiscal_position': None}}

        if not partner_id or not company_id or not fiscal_category_id:
            return result

        #TODO waiting migration super method to new api
        partner_invoice_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': company_id,
            'context': dict(self.env.context),
            'fiscal_category_id': fiscal_category_id,
        }
        return self._fiscal_position_map(result, **kwargs)

    def onchange_company_id(self, partner_id, company_id):

        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        #TODO waiting migration super method to new api
        partner_invoice_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': company_id,
            'context': self.env.context,
        }
        return self._fiscal_position_map(result, **kwargs)

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        result = {}

        comment = ''
        if picking.fiscal_position.inv_copy_note:
            comment += picking.fiscal_position.note or ''

        if picking.note:
            comment += ' - ' + picking.note

        result['partner_shipping_id'] = picking.partner_id.id

        result['comment'] = comment
        result['fiscal_category_id'] = picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position.id

        vals.update(result)
        return super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        readonly=True, states={'draft': [('readonly', False)],
            'sent': [('readonly', False)]})
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)],
            'sent': [('readonly', False)]})

    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        ctx.update({'use_domain': ('use_picking', '=', True)})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def onchange_product_id(self, product_id, location_id,
                            location_dest_id, partner_id):
        context = dict(self.env.context)
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        if context.get('company_id'):
            company_id = context['company_id']
        else:
            company_id = self.env.user.company_id.id

        result = {'value': {}}
        result['value']['invoice_state'] = context.get('parent_invoice_state')

        if parent_fiscal_category_id and product_id and partner_id:

            partner = self.env['res.partner'].browse(partner_id)
            obj_fp_rule = self.env['account.fiscal.position.rule']
            product_fc_id = obj_fp_rule.product_fiscal_category_map(
                product_id, parent_fiscal_category_id, partner.state_id.id)

            if product_fc_id:
                parent_fiscal_category_id = product_fc_id

            result['value']['fiscal_category_id'] = parent_fiscal_category_id

            kwargs = {
                'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'partner_shipping_id': partner_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'company_id': company_id,
                'context': context
            }

            result.update(self._fiscal_position_map(result, **kwargs))

        result_super = super(StockMove, self).onchange_product_id(
            product_id, location_id, location_dest_id, partner_id)

        if result_super.get('value'):
            result_super.get('value').update(result['value'])
        else:
            result_super.update(result)
        return result_super

    @api.multi
    def onchange_fiscal_category_id(self, fiscal_category_id, partner_id,
                                    company_id):

        result = {'value': {'fiscal_position': None}}

        if not partner_id or not company_id or not fiscal_category_id:
            return result

        #TODO waiting migration super method to new api
        partner_invoice_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['invoice'])['invoice']
        partner_shipping_id = self.pool.get('res.partner').address_get(
            self._cr, self._uid, [partner_id], ['delivery'])['delivery']

        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': company_id,
            'context': dict(self.env.context),
            'fiscal_category_id': fiscal_category_id,
        }
        return self._fiscal_position_map(result, **kwargs)

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        result = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        fiscal_position = move.fiscal_position or \
            move.picking_id.fiscal_position
        fiscal_category_id = move.fiscal_category_id or \
            move.picking_id.fiscal_category_id

        result['cfop_id'] = fiscal_position.cfop_id.id
        result['fiscal_category_id'] = fiscal_category_id.id
        result['fiscal_position'] = fiscal_position.id

        # TODO este código é um fix pq no core nao se copia os impostos
        ctx = dict(self.env.context)
        ctx['fiscal_type'] = move.product_id.fiscal_type
        ctx['product_id'] = move.product_id.id

        if inv_type in ('out_invoice', 'in_refund'):
            ctx['type_tax_use'] = 'sale'
            taxes = move.product_id.taxes_id
        else:
            ctx['type_tax_use'] = 'sale'
            taxes = move.product_id.supplier_taxes_id

        if fiscal_position:
            taxes = fiscal_position.with_context(ctx).map_tax(taxes)
        result['invoice_line_tax_id'] = [[6, 0, taxes.ids]]
        ##############

        if fiscal_position:
            account_id = result.get('account_id')
            account_id = fiscal_position.map_account(account_id)

        return result

    @api.cr_uid_ids_context
    def _picking_assign(self, cr, uid, move_ids, procurement_group, location_from, location_to, context=None):
        result = super(StockMove, self)._picking_assign(
            cr, uid, move_ids, procurement_group, location_from, location_to, context)
        if move_ids:
            move = self.browse(cr, uid, move_ids, context=context)[0]
            if move.picking_id:
                picking_values = {
                    'fiscal_category_id': move.fiscal_category_id.id,
                    'fiscal_position': move.fiscal_position.id,
                }
                self.pool.get("stock.picking").write(
                    cr, uid, move.picking_id.id, picking_values, context=context)
        return result