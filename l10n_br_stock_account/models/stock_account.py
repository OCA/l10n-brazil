# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _default_fiscal_category(self):
        return self.env.user.company_id.stock_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, domain="[('state', '=', 'approved')]",
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)]})

    def _fiscal_position_map(self, **kwargs):
        ctx = dict(self.env.context)
        if ctx.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({'use_domain': ('use_picking', '=', True)})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(**kwargs)

    @api.onchange('fiscal_category_id', 'company_id')
    def onchange_fiscal(self):
        if self.partner_id and self.company_id and self.fiscal_category_id:
            kwargs = {
                'partner_id': self.partner_id,
                'partner_invoice_id': self.partner_id,
                'partner_shipping_id': self.partner_id,
                'company_id': self.company_id,
                'context': dict(self.env.context),
                'fiscal_category_id': self.fiscal_category_id,
            }
            obj_fiscal_position = self._fiscal_position_map(**kwargs)
            if obj_fiscal_position:
                self.fiscal_position_id = obj_fiscal_position.id


class StockMove(models.Model):
    _inherit = "stock.move"

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal', readonly=True,
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]})
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position', readonly=True,
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]})

    def _fiscal_position_map(self, **kwargs):
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_picking', '=', True)})

        partner = kwargs.get('partner_id')
        obj_fp_rule = self.env['account.fiscal.position.rule']
        product_fc_id = obj_fp_rule.with_context(
            ctx).product_fiscal_category_map(
            kwargs.get('product_id'),
            kwargs.get('fiscal_category_id'),
            partner.state_id.id)

        if product_fc_id:
            kwargs['fiscal_category_id'] = product_fc_id

        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(**kwargs)

    @api.onchange('product_id')
    def onchange_product_id(self):
        context = dict(self.env.context)
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        if context.get('company_id'):
            company_id = context['company_id']
        else:
            company_id = self.env.user.company_id.id

        result = {'value': {}}
        result['value']['invoice_state'] = context.get('parent_invoice_state')

        if parent_fiscal_category_id and self.product_id and self.partner_id:

            kwargs = {
                'partner_id': self.partner_id,
                'product_id': self.product_id,
                'partner_invoice_id': self.partner_id,
                'partner_shipping_id': self.partner_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'company_id': company_id,
                'context': context
            }

            result.update(self._fiscal_position_map(**kwargs))

        result_super = super(StockMove, self).onchange_product_id()
        if result_super.get('value'):
            result_super.get('value').update(result['value'])
        else:
            result_super.update(result)
        return result_super

    @api.onchange('fiscal_category_id', 'fiscal_position_id')
    def onchange_fiscal(self):
        if self.picking_id.partner_id and self.picking_id.company_id \
                and self.fiscal_category_id:
            kwargs = {
                'partner_id': self.picking_id.partner_id,
                'product_id': self.product_id,
                'partner_invoice_id': self.picking_id.partner_id,
                'partner_shipping_id': self.picking_id.partner_id,
                'company_id': self.picking_id.company_id,
                'context': dict(self.env.context),
                'fiscal_category_id': self.fiscal_category_id,
            }
            fiscal_position = self._fiscal_position_map(**kwargs)
            if fiscal_position:
                self.fiscal_position_id = fiscal_position.id

    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited. """
        result = super(StockMove, self)._get_new_picking_values()
        result.update({
            'fiscal_category_id': self.fiscal_category_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
        })
        return result
