# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = [_name, 'l10n_br_fiscal.document.line.mixin']

    def _get_protected_fields(self):
        protected_fields = super(SaleOrderLine, self)._get_protected_fields()
        return protected_fields + [
            'fiscal_tax_ids', 'operation_id', 'operation_line_id']

    @api.model
    def _default_operation(self):
        return self.env.user.company_id.sale_fiscal_operation_id

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        default=_default_operation,
        domain=lambda self: self._operation_domain())

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_sale_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes')

    quantity = fields.Float(
        related='product_uom_qty',
        depends=['product_uom_qty'])

    uom_id = fields.Many2one(
        related='product_uom',
        depends=['product_uom'])

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

    @api.depends(
        'product_uom_qty',
        'price_unit',
        'discount',
        'fiscal_price',
        'fiscal_quantity',
        'discount_value',
        'freight_value',
        'insurance_value',
        'other_costs_value',
        'tax_id')
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        super(SaleOrderLine, self)._compute_amount()
        for line in self:
            line._update_taxes()
            price_tax = line.price_tax + line.amount_tax_not_included
            price_subtotal = (
                line.price_subtotal + line.freight_value +
                line.insurance_value + line.other_costs_value)

            line.update({
                'price_tax': price_tax,
                'price_gross': price_subtotal + line.discount_value,
                'price_subtotal': price_subtotal,
                'price_total': price_subtotal + price_tax,
            })

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        result.update(self._prepare_br_fiscal_dict())
        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()

    @api.onchange('discount')
    def _onchange_discount(self):
        """Update discount value"""
        if self.env.user.has_group('l10n_br_sale.group_discount_per_value'):
            if self.discount:
                self.discount_value = (
                    self.price_gross * (self.discount / 100))

    @api.onchange('discount')
    def _onchange_discount(self):
        """Update discount percent"""

        # else:
        #     if self.discount:
        #         self.discount_value = (
        #             self.product_uom_qty *
        #             (self.price_unit * ((self.discount or 0.0) / 100.0))
        #         )

    @api.onchange('fiscal_tax_ids')
    def _onchange_fiscal_tax_ids(self):
        self.tax_id |= self.fiscal_tax_ids.account_taxes()
