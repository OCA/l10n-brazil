# -*- coding: utf-8 -*-
# @ 2014 Akretion - www.akretion.com.br -
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        for record in self:
            price = record._calc_line_base_price()
            qty = record._calc_line_quantity()
            taxes = record.tax_id.compute_all(
                price_unit=price,
                quantity=qty,
                product=record.product_id,
                partner=record.order_id.partner_invoice_id,
                fiscal_position=record.fiscal_position_id,
                insurance_value=record.insurance_value,
                freight_value=record.freight_value,
                other_costs_value=record.other_costs_value)

            record.price_subtotal = \
                record.order_id.pricelist_id.currency_id.round(
                    taxes['total_excluded'])
            record.price_gross = record._calc_price_gross(qty)
            record.discount_value = \
                record.order_id.pricelist_id.currency_id.round(
                    record.price_gross - (price * qty))

    insurance_value = fields.Float(
        string='Insurance',
        default=0.0,
        digits=dp.get_precision('Account'))
    other_costs_value = fields.Float(
        string='Other costs',
        default=0.0,
        digits=dp.get_precision('Account'))
    freight_value = fields.Float(
        string='Freight',
        default=0.0,
        digits=dp.get_precision('Account'))
    discount_value = fields.Float(
        compute='_amount_line',
        string='Vlr. Desc. (-)',
        digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(
        compute='_amount_line',
        string='Vlr. Bruto',
        digits=dp.get_precision('Sale Price'))
    price_subtotal = fields.Float(
        compute='_amount_line',
        string='Subtotal',
        digits=dp.get_precision('Sale Price'))
    customer_order = fields.Char(
        string=u"Pedido do Cliente",
        size=15)
    customer_order_line = fields.Char(
        string=u"Item do Pedido do Cliente",
        size=6)

    @api.onchange("customer_order_line")
    def _check_customer_order_line(self):
        if (self.customer_order_line and
                not self.customer_order_line.isdigit()):
            raise ValidationError(
                _(u"Customer order line must be "
                  "a number with up to six digits")
            )

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = super(
            SaleOrderLine, self)._prepare_invoice_line(qty)

        result['insurance_value'] = self.insurance_value
        result['other_costs_value'] = self.other_costs_value
        result['freight_value'] = self.freight_value
        result['partner_order'] = self.customer_order
        result['partner_order_line'] = self.customer_order_line

        if self.product_id.fiscal_type == 'product':
            if self.fiscal_position_id:
                cfop = self.fiscal_position_id.cfop_id
                if cfop:
                    result['cfop_id'] = cfop.id
        return result
