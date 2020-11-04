# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = [_name, 'l10n_br_fiscal.document.line.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.sale_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain())

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_sale_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes',
    )

    quantity = fields.Float(
        related='product_uom_qty',
        depends=['product_uom_qty'],
    )

    uom_id = fields.Many2one(
        related='product_uom',
        depends=['product_uom'],
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='order_id.company_id.tax_framework',
        string='Tax Framework',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Partner',
    )

    # Add Fields in model sale.order.line
    price_gross = fields.Monetary(
        compute='_compute_amount',
        string='Gross Amount',
        default=0.00,
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='sale_order_line_comment_rel',
        column1='sale_line_id',
        column2='comment_id',
        string='Comments',
    )

    def _get_protected_fields(self):
        protected_fields = super()._get_protected_fields()
        return protected_fields + [
            'fiscal_tax_ids', 'fiscal_operation_id',
            'fiscal_operation_line_id',
        ]

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
        super()._compute_amount()
        for l in self:
            l._update_taxes()
            price_tax = l.price_tax + l.amount_tax_not_included
            price_total = (
                l.price_subtotal + l.freight_value +
                l.insurance_value + l.other_costs_value)

            l.update({
                'price_tax': price_tax,
                'price_gross': l.price_subtotal + l.discount_value,
                'price_total': price_total + price_tax,
            })

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        result = self._prepare_br_fiscal_dict()
        result.update(super()._prepare_invoice_line(qty))
        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def _onchange_product_uom(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()

    @api.onchange('discount')
    def _onchange_discount_percent(self):
        """Update discount value"""
        if not self.env.user.has_group('l10n_br_sale.group_discount_per_value'):
            if self.discount:
                self.discount_value = (
                    (self.product_uom_qty * self.price_unit)
                    * (self.discount / 100)
                )

    @api.onchange('discount_value')
    def _onchange_discount_value(self):
        """Update discount percent"""
        if self.env.user.has_group('l10n_br_sale.group_discount_per_value'):
            if self.discount_value:
                self.discount = ((self.discount_value * 100) /
                                 (self.product_uom_qty * self.price_unit))

    @api.onchange('fiscal_tax_ids')
    def _onchange_fiscal_tax_ids(self):
        super()._onchange_fiscal_tax_ids()
        self.tax_id |= self.fiscal_tax_ids.account_taxes()
