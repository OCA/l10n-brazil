# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DocumentCorrectionWizard(models.TransientModel):
    _inherit = 'l10n_br_fiscal.document.correction.wizard'

    @api.multi
    def doit(self):
        # TODO refactoring in fiscal event PR
        for wizard in self:
            document = self.env[self.env.context["active_model"]].browse(
                self.env.context["active_id"])

            if self.env.context["active_model"] == 'account.invoice':
                fiscal_document = document.fiscal_document_id
            else:
                fiscal_document = document

            fiscal_document.correction_reason = wizard.justificative
            msg = "Carta de correção: {}".format(wizard.justificative)
            fiscal_document.message_post(body=msg)

            numeros = fiscal_document.fiscal_document_event_ids.filtered(
                lambda e: e.type == '14').mapped(
                'correction_document_event_id.sequencia')
            sequencia = str(int(max(numeros)) + 1) if numeros else '1'

            carta = self.env[
                'l10n_br_fiscal.document.correction'].create({
                    'document_id': fiscal_document.id,
                    'justificative': wizard.justificative,
                    'sequencia': sequencia,
                })
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '14',
                'response': 'Correção da NFe %s' % fiscal_document.key,
                'company_id': fiscal_document.company_id.id,
                'origin': 'NFe-%s' % fiscal_document.number,
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'correction_document_event_id': carta.id,
                'fiscal_document_id': fiscal_document.id,
            })

            carta.correction(event_id)
        return {'type': 'ir.actions.act_window_close'}
