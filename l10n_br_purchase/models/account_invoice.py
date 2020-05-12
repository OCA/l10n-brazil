# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        result = super(
            AccountInvoice, self
        )._prepare_invoice_line_from_po_line(line)

        # To create a new fiscal document line
        result['fiscal_document_line_id'] = False

        # fiscal document line fields
        result['operation_id'] = line.operation_id.id
        result['operation_line_id'] = line.operation_line_id.id
        result["freight_value"] = line.freight_value
        result["insurance_value"] = line.insurance_value
        result["other_costs_value"] = line.other_costs_value
        result["partner_order"] = line.partner_order
        result["partner_order_line"] = line.partner_order_line
        result['amount_tax_not_included'] = line.amount_tax_not_included
        result['amount_tax_withholding'] = line.amount_tax_withholding

        return result
