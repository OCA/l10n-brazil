from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def get_invoice_fiscal_number(self):
        self.ensure_one()
        return self.document_number
