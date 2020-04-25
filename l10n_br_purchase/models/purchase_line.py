# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'l10n_br_fiscal.document.line.mixin']

    quantity = fields.Float(
        related='product_qty'
    )

    uom_id = fields.Many2one(
        related='product_uom'
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_sale_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes'
    )

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(
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
