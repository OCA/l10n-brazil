# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'l10n_br_fiscal.document.line.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.purchase_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ('state', '=', 'approved'),
            ('fiscal_type', 'in', ('purchase', 'other', 'purchase_refund'))]
        return domain

    # Adapt Mixin's fields
    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_purchase_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes',
    )

    quantity = fields.Float(
        string='Mixin Quantity',
        related='product_uom_qty',
    )

    uom_id = fields.Many2one(
        string='Mixin UOM',
        related='product_uom',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="order_id.company_id.tax_framework",
        string="Tax Framework",
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Partner',
    )

    @api.depends('product_qty', 'price_unit',  'taxes_id')
    def _compute_amount(self):
        """Compute the amounts of the PO line."""
        super(PurchaseOrderLine, self)._compute_amount()
        for line in self:
            line._update_taxes()
            price_tax = line.price_tax + line.amount_tax_not_included
            price_subtotal = (
                line.price_subtotal + line.freight_value +
                line.insurance_value + line.other_costs_value)

            line.update({
                'price_tax': price_tax,
                'price_subtotal': price_subtotal,
                'price_total': price_subtotal + price_tax,
            })

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        super(PurchaseOrderLine, self)._onchange_quantity()
        self._onchange_commercial_quantity()

    @api.onchange('fiscal_tax_ids')
    def _onchange_fiscal_tax_ids(self):
        self.taxes_id |= self.fiscal_tax_ids.account_taxes()
