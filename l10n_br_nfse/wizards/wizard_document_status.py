# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WizardDocumentStatus(models.TransientModel):
    _name = 'l10n_br_fiscal.document.status.wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    rps_number = fields.Char(
        string='RPS Number',
        default=lambda self: self.env[
            self._context.get('active_model')
        ].browse(self._context.get('active_ids', [])).rps_number
    )

    @api.multi
    def get_document_status(self):
        self.write({
            "document_status": self.document_id.action_consultar_nfse_rps(),
            "rps_number": self.document_id.rps_number,
            "state": "done",
        })
        return self._reopen()

    @api.multi
    def doit(self):
        for wizard in self:
            if wizard.document_id:
                return wizard.get_document_status()
        self._close()