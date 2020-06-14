# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class FiscalDocument(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    @api.multi
    def unlink(self):
        invoices = self.env['account.invoice'].search(
            [('fiscal_document_id', 'in', self.ids)])
        invoices.unlink()
        return super().unlink()
