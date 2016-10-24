# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _default_fiscal_category(self):
        return self.env.user.company_id.stock_fiscal_category_id

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

    @api.onchange('fiscal_category_id', 'company_id')
    def onchange_fiscal(self):
        if self.partner_id and self.company_id and self.fiscal_category_id:
            result = {'value': {'fiscal_position': None}}
            kwargs = {
                'partner_id': self.partner_id.id,
                'partner_invoice_id': self.partner_id.id,
                'partner_shipping_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'context': dict(self.env.context),
                'fiscal_category_id': self.fiscal_category_id.id,
            }
            result = self._fiscal_position_map(result, **kwargs)
            self.fiscal_position = result['value'].get('fiscal_position')

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        result = {}

        comment = ''
        if picking.fiscal_position.inv_copy_note:
            comment += picking.fiscal_position.note or ''
        if picking.sale_id and picking.sale_id.copy_note:
            comment += picking.sale_id.note or ''
        if picking.note:
            comment += ' - ' + picking.note

        result['partner_shipping_id'] = picking.partner_id.id

        result['comment'] = comment
        result['fiscal_category_id'] = picking.fiscal_category_id.id
        result['fiscal_position'] = picking.fiscal_position.id

        if picking.fiscal_category_id.journal_type in ('sale_refund',
                                                       'purchase_refund'):
            result['nfe_purpose'] = '4'

        vals.update(result)
        return super(StockPicking, self)._create_invoice_from_picking(picking,
                                                                      vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal', readonly=True,
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]})
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position', readonly=True,
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]})

    @api.model
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_picking', '=', True)})

        partner = self.env['res.partner'].browse(kwargs.get('partner_id'))
        obj_fp_rule = self.env['account.fiscal.position.rule']
        product_fc_id = obj_fp_rule.with_context(
            ctx).product_fiscal_category_map(
            kwargs.get('product_id'),
            kwargs.get('fiscal_category_id'),
            partner.state_id.id)

        if product_fc_id:
            kwargs['fiscal_category_id'] = product_fc_id
            result['value']['fiscal_category_id'] = product_fc_id
        else:
            result['value']['fiscal_category_id'] = kwargs.get(
                'fiscal_category_id')

        return obj_fp_rule.with_context(ctx).apply_fiscal_mapping(
            result, **kwargs)

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

            kwargs = {
                'partner_id': partner_id,
                'product_id': product_id,
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

    @api.onchange('fiscal_category_id', 'fiscal_position')
    def onchange_fiscal(self):
        if self.picking_id.partner_id and self.picking_id.company_id \
                and self.fiscal_category_id:
            result = {'value': {'fiscal_position': None}}
            kwargs = {
                'partner_id': self.picking_id.partner_id.id,
                'product_id': self.product_id.id,
                'partner_invoice_id': self.picking_id.partner_id.id,
                'partner_shipping_id': self.picking_id.partner_id.id,
                'company_id': self.picking_id.company_id.id,
                'context': dict(self.env.context),
                'fiscal_category_id': self.fiscal_category_id.id,
            }
            result = self._fiscal_position_map(result, **kwargs)
            self.fiscal_position = result['value'].get('fiscal_position')
            self.fiscal_category_id = result['value'].get('fiscal_category_id')

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
        ctx['partner_id'] = partner.id

        # Required to compute_all in account.invoice.line
        result['partner_id'] = partner.id

        ctx['product_id'] = move.product_id.id

        if inv_type in ('out_invoice', 'in_refund'):
            ctx['type_tax_use'] = 'sale'
            taxes = move.product_id.taxes_id
        else:
            ctx['type_tax_use'] = 'purchase'
            taxes = move.product_id.supplier_taxes_id

        if fiscal_position:
            taxes = fiscal_position.with_context(ctx).map_tax(taxes)
        result['invoice_line_tax_id'] = [[6, 0, taxes.ids]]

        if fiscal_position:
            account_id = result.get('account_id')
            account_id = fiscal_position.map_account(account_id)

        return result

    @api.cr_uid_ids_context
    def _picking_assign(self, cr, uid, move_ids, procurement_group,
                        location_from, location_to, context=None):

        result = super(StockMove, self)._picking_assign(
            cr, uid, move_ids, procurement_group,
            location_from, location_to, context)
        if move_ids:
            move = self.browse(cr, uid, move_ids, context=context)[0]
            if move.picking_id:
                picking_values = {
                    'fiscal_category_id': move.fiscal_category_id.id,
                    'fiscal_position': move.fiscal_position.id,
                }
                self.pool.get("stock.picking").write(
                    cr, uid, move.picking_id.id,
                    picking_values, context=context)
        return result
