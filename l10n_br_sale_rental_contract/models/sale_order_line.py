# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

# values that come from the sale_rental_contract line, not from the fiscal dict
NON_FISCAL_KEYS = ("name", "product_id", "quantity", "price_unit", "uom_id")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_contract_line_values(
        self, contract, predecessor_contract_line_id=False
    ):
        values = super()._prepare_contract_line_values(
            contract, predecessor_contract_line_id
        )
        if not (self._is_rental_contract_line() and self.fiscal_operation_id):
            return values
        # l10n_br_product_contract takes the fiscal values of the order line,
        # computed on days x daily price: recompute them for the monthly line
        fiscal_values = self._prepare_br_fiscal_dict()
        virtual = self.env["l10n_br_fiscal.document.line"].new(fiscal_values)
        virtual.quantity = values["quantity"]
        virtual.price_unit = values["price_unit"]
        virtual.uom_id = values["uom_id"]
        values.update(
            {
                fname: virtual._fields[fname].convert_to_write(virtual[fname], virtual)
                for fname in fiscal_values
                if fname not in NON_FISCAL_KEYS
            }
        )
        return values
