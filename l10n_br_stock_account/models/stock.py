# -*- coding: utf-8 -*-
# Copyright (C) 2016  Renato Lima - Akretion
# Copyright (C) 2016  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class StockLocationPath(models.Model):
    _inherit = 'stock.location.path'

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal',
        domain="[('state', '=', 'approved')]")

    @api.model
    def _prepare_push_apply(self, rule, move):
        result = super(StockLocationPath, self)._prepare_push_apply(rule, move)
        if rule.fiscal_category_id:

            ctx = dict(self.env.context)
            ctx.update({'use_domain': ('use_picking', '=', True)})

            kwargs = {
                'partner_id': move.picking_id.partner_id.id,
                'product_id': move.product_id.id,
                'partner_invoice_id': move.picking_id.partner_id.id,
                'partner_shipping_id': move.picking_id.partner_id.id,
                'fiscal_category_id': rule.fiscal_category_id.id,
                'company_id': rule.company_id.id,
                'context': ctx
            }

            partner = move.picking_id.partner_id
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

            result_fr = obj_fp_rule.with_context(ctx).apply_fiscal_mapping(
                {'value': {}}, **kwargs)

            result.update({
                'fiscal_position': result_fr['value']['fiscal_position']})
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
