# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        """l10n_br_sale splits the invoices by document type: the rental charge
        (NFS-e) comes apart from the goods sold (NF-e) but takes the order
        operation (sale); when all its lines are rental, use the rental one."""
        values = super()._prepare_invoice()
        lines = self._get_invoiceable_lines().filtered(
            lambda line: not line.display_type and not line.is_downpayment
        )
        operations = lines.mapped("fiscal_operation_id")
        rental_operation = self.company_id._l10n_br_rental_operation("rental")
        if lines and rental_operation and operations == rental_operation:
            values["fiscal_operation_id"] = rental_operation.id
            if rental_operation.journal_id:
                values["journal_id"] = rental_operation.journal_id.id
        return values
