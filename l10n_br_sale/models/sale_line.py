# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _calc_line_base_price(self):
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    def _calc_line_quantity(self):
        return self.product_uom_qty

    def _calc_price_gross(self, qty):
        return self.price_unit * qty

    @api.multi
    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        for record in self:
            price = record._calc_line_base_price()
            qty = record._calc_line_quantity()
            taxes = record.tax_id.compute_all(
                price, quantity=qty,
                product=record.product_id,
                partner=record.order_id.partner_invoice_id)

            record.price_subtotal = \
                record.order_id.pricelist_id.currency_id.round(
                    taxes['total_excluded'])
            record.price_gross = record._calc_price_gross(qty)
            record.discount_value = \
                record.order_id.pricelist_id.currency_id.round(
                    record.price_gross - (price * qty))

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True, oldname='fiscal_position',
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)]
        }
    )
    discount_value = fields.Float(compute='_amount_line',
                                  string='Vlr. Desc. (-)',
                                  digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(
        compute='_amount_line', string='Vlr. Bruto',
        digits=dp.get_precision('Sale Price'))
    price_subtotal = fields.Float(
        compute='_amount_line', string='Subtotal',
        digits=dp.get_precision('Sale Price'))

    @api.model
    def _fiscal_position_map(self, **kwargs):
        result = {'value': {}}
        context = dict(self.env.context)
        context.update({'use_domain': ('use_sale', '=', True)})
        fp_rule_obj = self.env['account.fiscal.position.rule']

        partner_invoice = kwargs.get('partner_invoice_id')

        product_fc_id = fp_rule_obj.with_context(
            context).product_fiscal_category_map(
                kwargs.get('product_id'),
                kwargs.get('fiscal_category_id'),
                partner_invoice.state_id.id)

        if product_fc_id:
            kwargs['fiscal_category_id'] = product_fc_id

        result['value']['fiscal_category_id'] = kwargs.get(
            'fiscal_category_id')

        obj_fiscal_position = fp_rule_obj.with_context(
            context).apply_fiscal_mapping(**kwargs)
        obj_product = kwargs.get('product_id')

        if obj_product and obj_fiscal_position:
            result['value']['fiscal_position_id'] = obj_fiscal_position
            context.update({
                'fiscal_type': obj_product.fiscal_type,
                'type_tax_use': 'sale', 'product_id': obj_product.id})
            taxes = obj_product.taxes_id
            tax_ids = obj_fiscal_position.with_context(context).map_tax(
                taxes, obj_product, partner_invoice)
            result['value']['tax_id'] = tax_ids

        return result

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        for record in self:
            context = dict(record.env.context)
            record = record.with_context(context)
            parent_fiscal_category_id = record.order_id.fiscal_category_id
            company_id = record.order_id.company_id
            partner_invoice_id = record.order_id.partner_invoice_id
            result = {'value': {}}
            if parent_fiscal_category_id and record.product_id and\
                    partner_invoice_id and company_id:
                kwargs = {
                    'company_id': company_id,
                    'partner_id': record.order_id.partner_id,
                    'product_id': record.product_id,
                    'partner_invoice_id': partner_invoice_id,
                    'fiscal_category_id': parent_fiscal_category_id,
                    'context': context
                }
                result.update(record._fiscal_position_map(**kwargs))
                context.update({
                    'fiscal_type': record.product_id.fiscal_type,
                    'type_tax_use': 'sale',
                    'product_id': record.product_id
                })
            result_super = super(SaleOrderLine, record).product_id_change()
            if result['value']:
                record.update(result['value'])
            return result_super

    @api.multi
    @api.onchange('fiscal_category_id', 'fiscal_position_id')
    def onchange_fiscal(self):
        for record in self:
            if record.order_id.company_id and record.order_id.partner_id \
                    and record.fiscal_category_id:
                kwargs = {
                    'company_id': record.order_id.company_id,
                    'partner_id': record.order_id.partner_id,
                    'partner_invoice_id': record.order_id.partner_invoice_id,
                    'product_id': record.product_id,
                    'fiscal_category_id': record.fiscal_category_id or
                    record.order_id.fiscal_category_id,
                    'context': record.env.context
                }
                result = record._fiscal_position_map(**kwargs)

                kwargs.update({
                    'fiscal_category_id': record.fiscal_category_id.id,
                    'fiscal_position_id': record.fiscal_position_id.id,
                    'tax_id': [(6, 0, record.tax_id.ids)],
                })
                record.update(result['value'])

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        result['fiscal_category_id'] = \
            self.fiscal_category_id.id or self.order_id.fiscal_category_id.id \
            or False
        result['fiscal_position_id'] = self.fiscal_position_id.id or \
            self.order_id.fiscal_position_id.id or False
        return result
