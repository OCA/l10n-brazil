# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleInvoicePlan(models.Model):
    _inherit = "sale.invoice.plan"

    def _compute_new_invoice_quantity(self, invoice_move):
        result = super()._compute_new_invoice_quantity(invoice_move=invoice_move)

        if invoice_move:
            for line in invoice_move.invoice_line_ids:
                line.write({"fiscal_quantity": line.quantity})
                line._onchange_fiscal_tax_ids()
        return result
