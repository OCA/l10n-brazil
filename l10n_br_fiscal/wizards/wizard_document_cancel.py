# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentCancelWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.document.cancel.wizard'
    _description = 'Fiscal Document Cancel Wizard'

    justificative = fields.Text(
        string='Justificativa',
        size=255,
        required=True)

    @api.multi
    @api.constrains('justificative')
    def _check_justificative(self):
        for record in self:
            if len(record.justificative) < 15:
                raise ValidationError(
                    _('Justificativa deve ter o tamanho mínimo de 15 '
                      'caracteres.'))

    @api.multi
    def doit(self):
        for wizard in self:
            document_id = self.env[self.env.context["active_model"]].browse(
                self.env.context["active_id"]
            )

            cancel = self.env[
                'l10n_br_fiscal.document.cancel'].create({
                    'document_id': document_id.id,
                    'justificative': wizard.justificative,
                })
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '2',
                'response': 'Cancelamento da NFe %s' % document_id.key,
                'company_id': document_id.company_id.id,
                'origin': 'NFe-%s' % document_id.number,
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'cancel_document_event_id': cancel.id,
                'fiscal_document_event_id': document_id.id,
            })

            cancel.cancel_document(event_id)
        return {"type": "ir.actions.act_window_close"}
