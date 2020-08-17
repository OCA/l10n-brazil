# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WizardDocumentStatus(models.TransientModel):

    _inherit = 'l10n_br_fiscal.document.status.wizard'

    rps_number = fields.Char(
        string='RPS Number',
        default=lambda self: self.env['l10n_br_fiscal.document'].browse(
            self._context.get('active_ids', [])).rps_number
    )

    @api.multi
    def get_document_status(self):
        for data in self:
            document_id = self.env['l10n_br_fiscal.document'].browse(
                self._context.get('active_ids', []))[0]
            call_result = {
                "document_status": document_id.action_consultar_nfse_rps(),
                "rps_number": data.rps_number,
                "state": "done",
            }
            data.write(call_result)

            return {
                "name": "Fiscal Document Inquiry",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "l10n_br_fiscal.document.status.wizard",
                "res_id": data.id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": data.env.context,
            }
