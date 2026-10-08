# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _l10n_br_rental_line_operation(self, product, order):
        """Rental service lines (new rental or extension) are charged with the
        rental operation, not the sale operation of the order."""
        if not product.rented_product_id:
            return self.env["l10n_br_fiscal.operation"]
        company = order.company_id or self.env.company
        return company._l10n_br_rental_operation("rental")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("product_id") or not vals.get("order_id"):
                continue
            operation = self._l10n_br_rental_line_operation(
                self.env["product.product"].browse(vals["product_id"]),
                self.env["sale.order"].browse(vals["order_id"]),
            )
            if operation:
                vals["fiscal_operation_id"] = operation.id
        return super().create(vals_list)

    @api.onchange("product_id")
    def _onchange_product_id_l10n_br_rental(self):
        operation = self._l10n_br_rental_line_operation(self.product_id, self.order_id)
        if operation:
            self.fiscal_operation_id = operation
