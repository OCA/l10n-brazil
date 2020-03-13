# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from ...l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK,
)


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'l10n_br_fiscal.document.line.mixin']

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

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="order_id.partner_id",
        string="Partner")

    discount_value = fields.Float(
        compute='_amount_line',
        string='Vlr. Desc. (-)',
        digits=dp.get_precision('Sale Price'))

    price_gross = fields.Float(
        compute='_amount_line', string='Vlr. Bruto',
        digits=dp.get_precision('Sale Price'))

    price_subtotal = fields.Float(
        compute='_amount_line', string='Subtotal',
        digits=dp.get_precision('Sale Price'))

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_sale_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes")

    # Create to avoid error l10n_br_fiscal/models/
    # document_fiscal_line_mixin.py", line 548, in _compute_taxes
    quantity = fields.Float(
        related='product_uom_qty',
        string="Quantity",
        digits=dp.get_precision("Product Unit of Measure"))

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="order_id.company_id.tax_framework",
        string="Tax Framework")

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        result['operation_id'] = \
            self.operation_id.id or self.order_id.operation_id.id \
            or False
        result['operation_line_id'] = self.operation_line_id.id or \
            False
        return result
