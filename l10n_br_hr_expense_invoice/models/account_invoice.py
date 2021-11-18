# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.onchange("partner_id")
    def _onchange_expense_invoice_partner_id(self):
        self._onchange_fiscal_operation_id()
        for line in self.invoice_line_ids:
            price_unit = line.price_unit
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_taxes()
            line._onchange_product_id()
            line.price_unit = price_unit
