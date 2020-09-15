# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardDocumentInvalidate(models.TransientModel):

    _name = "l10n_br_fiscal.wizard_document_invalidate"
    _description = "Document fiscal cancel wizard"

    justificative = fields.Text("Justificativa", size=255, required=True)

    @api.constrains("justificative")
    @api.multi
    def _check_justificative(self):
        for record in self:
            if len(record.justificative) < 15:
                raise UserError(
                    _("Justificativa deve ter o tamanho mínimo de 15 " "caracteres.")
                )

    @api.multi
    def doit(self):
        for wizard in self:
            document_id = self.env[self.env.context["active_model"]].browse(
                self.env.context["active_id"]
            )

            inut = self.env[
                'l10n_br_fiscal.document.invalidate.number'].create({
                    'company_id': document_id.company_id.id,
                    'document_id': document_id.id,
                    'document_serie_id': document_id.document_serie_id.id,
                    'number_start': document_id.number,
                    'number_end': document_id.number,
                    'state': 'draft',
                    'justificative': wizard.justificative,
                })
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '3',
                'response': 'Inutilização do número %s ao número %s' % (
                    document_id.number, document_id.number),
                'company_id': document_id.company_id.id,
                'origin': 'NFe-%s' % document_id.number,
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'invalid_number_document_event_id': inut.id,
                'fiscal_document_id': document_id.id,
            })

            inut.invalidate(event_id)
        return {"type": "ir.actions.act_window_close"}
