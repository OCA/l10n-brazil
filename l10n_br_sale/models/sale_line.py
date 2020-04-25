# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'l10n_br_fiscal.document.line.mixin']

    def _get_protected_fields(self):
        protected_fields = super(SaleOrderLine, self)._get_protected_fields()
        return protected_fields + [
            'fiscal_tax_ids', 'operation_id', 'operation_line_id']

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_sale_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes')

    quantity = fields.Float(
        related='product_uom_qty')

    uom_id = fields.Many2one(
        related='product_uom')

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="order_id.company_id.tax_framework",
        string="Tax Framework")

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Partner')

    # Add Fields in model sale.order.line
    price_gross = fields.Monetary(
        compute='_compute_amount',
        string='Gross Amount',
        default=0.00)

    def _calc_line_base_price(self):
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    def _calc_line_quantity(self):
        return self.product_uom_qty

    @api.depends('product_uom_qty', 'discount', 'price_unit')
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        for line in self:
            line.tax_id |= line.fiscal_tax_ids.account_taxes()
            taxes = line.tax_id.compute_all(
                price_unit=line._calc_line_base_price(),
                currency=line.order_id.currency_id,
                quantity=line._calc_line_quantity(),
                product=line.product_id,
                partner=line.order_id.partner_id,
                fiscal_taxes=line.fiscal_tax_ids,
                operation_line=line.operation_line_id,
                ncm=line.ncm_id,
                nbm=line.nbm_id,
                cest=line.cest_id,
                discount_value=line.discount_value,
                insurance_value=line.insurance_value,
                other_costs_value=line.other_costs_value,
                freight_value=line.freight_value,
                fiscal_price=line.fiscal_price,
                fiscal_quantity=line.fiscal_quantity,
                uot=line.uot_id,
                icmssn_range=line.icmssn_range_id)

            tax_not_included = sum(
                t.get('amount', 0.0)
                for t in taxes.get('taxes', []) if not t.get('tax_include'))

            line.update({
                'amount_tax_not_included': tax_not_included,
                'price_tax': tax_not_included,
                'price_gross': taxes['total_excluded'] + line.discount_value,
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        fiscal_operation = self.operation_id or self.order_id.operation_id

        if fiscal_operation:
            result['operation_id'] = fiscal_operation.id
            result['operation_line_id'] = self.operation_line_id.id
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

    @api.onchange('product_uom', 'product_uom_qty', 'price_unit')
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        super(SaleOrderLine, self).product_uom_change()
        self._onchange_commercial_quantity()

    @api.onchange('discount_value', 'discount')
    def _onchange_discount_value(self):
        """Update discount percent"""
        if self.env.user.has_group('l10n_br_sale.group_discount_per_value'):
            if self.discount_value:
                self.discount = (
                    abs(((self.price_subtotal / self.price_gross) * 100) - 1))
        else:
            if self.discount:
                self.discount_value = (
                    self.product_uom_qty *
                    (self.price_unit * ((self.discount or 0.0) / 100.0))
                )
