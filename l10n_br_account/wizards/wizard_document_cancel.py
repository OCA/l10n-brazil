# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DocumentCancelWizard(models.TransientModel):
    _inherit = 'l10n_br_fiscal.document.cancel.wizard'

    @api.multi
    def doit(self):
        for wizard in self:
            # TODO refactoring in fiscal event PR
            document = self.env[self.env.context["active_model"]].browse(
                self.env.context["active_id"])

            if self.env.context["active_model"] == 'account.invoice':
                invoice = document
                fiscal_document = invoice.fiscal_document_id
            else:
                fiscal_document = document
                invoice = self.env['account.invoice'].search(
                    [('fiscal_document_id', '=', fiscal_document.id)], limit=1)

            cancel = self.env[
                'l10n_br_fiscal.document.cancel'].create({
                    'document_id': fiscal_document.id,
                    'justificative': wizard.justificative,
                })
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '2',
                'response': 'Cancelamento da NFe %s' % fiscal_document.key,
                'company_id': fiscal_document.company_id.id,
                'origin': 'NFe-%s' % fiscal_document.number,
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'cancel_document_event_id': cancel.id,
                'fiscal_document_event_id': fiscal_document.id,
            })

            cancel.cancel_document(event_id)
            if invoice:
                invoice.action_cancel()
        return {"type": "ir.actions.act_window_close"}
