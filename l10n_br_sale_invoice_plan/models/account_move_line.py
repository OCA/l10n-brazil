# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _is_financial_only_line(self):
        """The line deducting the downpayment is not part of the fiscal document
        (the invoice of the installment carries the full value of the goods),
        but it must lower the amount to pay and the accounting entry."""
        res = super()._is_financial_only_line()
        if res or self.display_type != "product" or self.fiscal_document_line_id:
            return res
        return any(
            sale_line.is_downpayment and sale_line.order_id.use_invoice_plan
            for sale_line in self.sale_line_ids
        )
