# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models, fields

from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'l10n_br_fiscal.document.line.mixin']

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_purchase_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes')

    quantity = fields.Float(
        string='Mixin Quantity',
        related='product_uom_qty')

    uom_id = fields.Many2one(
        string='Mixin UOM',
        related='product_uom')

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="order_id.company_id.tax_framework",
        string="Tax Framework")

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Partner')

    @api.depends('product_qty', 'price_unit',  'taxes_id', 'fiscal_tax_ids')
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        for line in self:
            line.taxes_id |= line.fiscal_tax_ids.account_taxes()
            price = line.price_unit
            taxes = line.taxes_id.compute_all(
                price_unit=price,
                currency=line.order_id.currency_id,
                quantity=line.product_uom_qty,
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
            line.update({
                'price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        super(PurchaseOrderLine, self)._onchange_quantity()
        self._onchange_commercial_quantity()
