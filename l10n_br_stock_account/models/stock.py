# -*- coding: utf-8 -*-
# Copyright (C) 2016  Renato Lima - Akretion
# Copyright (C) 2016  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class StockLocationPath(models.Model):
    _inherit = 'stock.location.path'

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal',
        domain="[('state', '=', 'approved')]")

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        result = super(
            StockLocationPath, self)._prepare_move_copy_values(
            move_to_copy, new_date)
        if self.fiscal_category_id:
            ctx = dict(self.env.context)
            ctx.update({'use_domain': ('use_picking', '=', True)})

            kwargs = {
                'partner_id': move_to_copy.picking_id.partner_id,
                'product_id': move_to_copy.product_id,
                'partner_invoice_id': move_to_copy.picking_id.partner_id,
                'partner_shipping_id': move_to_copy.picking_id.partner_id,
                'fiscal_category_id': self.fiscal_category_id.id,
                'company_id': self.company_id.id,
                'context': ctx
            }

            partner = move_to_copy.picking_id.partner_id
            obj_fp_rule = self.env['account.fiscal.position.rule']
            product_fc_id = obj_fp_rule.with_context(
                ctx).product_fiscal_category_map(
                kwargs.get('product_id'),
                kwargs.get('fiscal_category_id'),
                partner.state_id.id)

            if product_fc_id:
                kwargs['fiscal_category_id'] = product_fc_id
                result['fiscal_category_id'] = product_fc_id
            else:
                result['fiscal_category_id'] = kwargs.get(
                    'fiscal_category_id')

            fiscal_position = obj_fp_rule.with_context(
                ctx).apply_fiscal_mapping(**kwargs)

            result.update({
                'fiscal_position_id': fiscal_position.id})
        return result


class ProcurementRule(models.Model):
    """
        Create relation with l10n-brazil fiscal category, used to select taxes
        on branch / inter company transfers.
    """
    _inherit = 'procurement.rule'

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal',
        domain="[('state', '=', 'approved')]",
    )
