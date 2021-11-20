# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleInvoicePlan(models.Model):

    _inherit = "sale.invoice.plan"

    @api.multi
    def _compute_new_invoice_quantity(self, invoice):

        super()._compute_new_invoice_quantity(invoice=invoice)

        if invoice:
            for line in invoice.invoice_line_ids:
                line.write({"fiscal_quantity": line.quantity})
                line._onchange_fiscal_tax_ids()
            invoice._onchange_invoice_line_ids()
