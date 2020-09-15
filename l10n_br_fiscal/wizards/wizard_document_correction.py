# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentCorrectionWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.document.correction.wizard'
    _description = 'Fiscal Document Correction Wizard'

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
            document_id = self.env[self.env.context['active_model']].browse(
                self.env.context['active_id'])

            document_id.correction_reason = wizard.justificative
            msg = "Carta de correção: {}".format(wizard.justificative)
            document_id.message_post(body=msg)

            numeros = document_id.fiscal_document_event_ids.filtered(
                lambda e: e.type == '14').mapped(
                'correction_document_event_id.sequencia')
            sequencia = str(int(max(numeros)) + 1) if numeros else '1'

            carta = self.env[
                'l10n_br_fiscal.document.correction'].create({
                    'document_id': document_id.id,
                    'justificative': wizard.justificative,
                    'sequencia': sequencia,
                })
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '14',
                'response': 'Correção da NFe %s' % document_id.key,
                'company_id': document_id.company_id.id,
                'origin': 'NFe-%s' % document_id.number,
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'correction_document_event_id': carta.id,
                'fiscal_document_id': document_id.id,
            })

            carta.correction(event_id)
        return {'type': 'ir.actions.act_window_close'}
