# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_contract_value(self, contract_template):
        """l10n_br_product_contract copies the order operation (sale) to the
        contract, and the contract invoice takes it: a contract made only of
        rental lines is a rental contract."""
        values = super()._prepare_contract_value(contract_template)
        contract_lines = self.order_line.filtered("product_id.is_contract")
        rental_operation = self.company_id._l10n_br_rental_operation("rental")
        if (
            contract_lines
            and rental_operation
            and all(line._is_rental_contract_line() for line in contract_lines)
        ):
            values["fiscal_operation_id"] = rental_operation.id
        return values
