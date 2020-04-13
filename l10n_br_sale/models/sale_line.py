# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

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

    @api.depends("price_unit", "tax_id", "discount", "product_uom_qty")
    def _amount_line(self):
        for record in self:
            price = record._calc_line_base_price()
            qty = record._calc_line_quantity()
            taxes = record.tax_id.compute_all(
                price_unit=price,
                quantity=qty,
                product=record.product_id,
                partner=record.order_id.partner_invoice_id,
                # TODO - The fields below are used in Base ICMS
                #  calculation https://github.com/OCA/l10n-brazil/blob/
                #  10.0/l10n_br_account_product/models/account_tax.py#L155
                # insurance_value=record.insurance_value,
                # freight_value=record.freight_value,
                # other_costs_value=record.other_costs_value,
            )

            record.price_subtotal = record.order_id.pricelist_id.currency_id.round(
                taxes["total_excluded"]
            )
            record.price_gross = record._calc_price_gross(qty)
            record.discount_value = record.order_id.pricelist_id.currency_id.round(
                record.price_gross - (price * qty)
            )

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
        result["insurance_value"] = self.insurance_value
        result["other_costs_value"] = self.other_costs_value
        result["freight_value"] = self.freight_value
        result["partner_order"] = self.partner_order
        result["partner_order_line"] = self.partner_order_line

        if self.product_id.fiscal_type == "product":
            if self.operation_line_id:
                cfop = self.operation_line_id.cfop_id
                if cfop:
                    result["cfop_id"] = cfop.id
        return result
