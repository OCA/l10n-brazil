# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class DocumentStatusWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.document.status.wizard'
    _description = 'Fiscal Document Status Wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    @api.multi
    def get_document_status(self):
        self.write({
            "document_status": self.document_id._document_status(),
            "state": "done",
        })
        return self._reopen()

    @api.multi
    def doit(self):
        for wizard in self:
            if wizard.document_id:
                return wizard.get_document_status()
        self._close()
