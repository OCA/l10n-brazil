# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        values = super()._prepare_invoice_line_from_po_line(line)
        values.update(line._prepare_br_fiscal_dict(default=True))
        return values
