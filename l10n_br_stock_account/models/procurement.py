# -*- coding: utf-8 -*-
# Copyright (C) 2016  Luis Felipe Mileo - KMEE                                #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class ProcurementOrder(models.Model):
    _name = "procurement.order"
    _inherit = [
        _name,
        "stock.invoice.state.mixin",
    ]

    @api.model
    def _get_stock_move_values(self):
        result = super(ProcurementOrder, self)._get_stock_move_values()
        if (self.rule_id and self.rule_id.fiscal_category_id and
                result['partner_id']):
            ctx = dict(self.env.context)
            ctx.update({'use_domain': ('use_picking', '=', True)})
            partner = self.env['res.partner'].browse(result['partner_id'])
            company = (self.warehouse_id.company_id or
                       self.company_id)
            kwargs = {
                'partner_id': partner,
                'product_id': self.product_id,
                'partner_invoice_id':  partner,
                # TODO: Implement fuction to compute partner invoice id
                'partner_shipping_id': partner,
                'fiscal_category_id': (
                    self.rule_id.fiscal_category_id
                ),
                'company_id': company,
                'context': ctx,
            }

            obj_fp_rule = self.env['account.fiscal.position.rule']
            product_fc_id = obj_fp_rule.with_context(
                ctx).product_fiscal_category_map(
                    kwargs.get('product_id'),
                    kwargs.get('fiscal_category_id'),
                    partner.state_id.id)

            if product_fc_id:
                kwargs['fiscal_category_id'] = product_fc_id
                result['fiscal_category_id'] = product_fc_id.id
            else:
                result['fiscal_category_id'] = kwargs.get(
                    'fiscal_category_id').id

            fiscal_position = obj_fp_rule.with_context(
                ctx).apply_fiscal_mapping(**kwargs)

            if fiscal_position:
                result.update({'fiscal_position_id': fiscal_position.id})

        return result
