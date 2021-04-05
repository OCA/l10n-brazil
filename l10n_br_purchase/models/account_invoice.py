# Copyright (C) 2020  Magno Costa - Akretion
# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        values = super()._prepare_invoice_line_from_po_line(line)
        values.update(line._prepare_br_fiscal_dict())
        return values

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self.purchase_id:
            self.fiscal_operation_id = self.purchase_id.fiscal_operation_id
            if not self.document_type_id:
                self.document_type_id = self.company_id.document_type_id
        return super().purchase_order_change()
