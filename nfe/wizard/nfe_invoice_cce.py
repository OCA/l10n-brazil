# -*- coding: utf-8 -*-
# Copyright (C) 2014   Matheus Lima Felix <matheus.felix@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from ..sped.nfe.processing.xml import send_correction_letter


class NfeInvoiceCce(models.TransientModel):

    _name = 'nfe.invoice_cce'

    mensagem = fields.Text('Mensagem', required=True)

    @api.multi
    def _check_name(self):

        for nfe in self:

            if not (len(nfe.mensagem) >= 15):
                return False

        return True

    _constraints = [
        (_check_name,
         'Tamanho de mensagem inválida !',
         ['mensagem'])]

    @api.multi
    def action_enviar_carta(self):

        correcao = self.mensagem
        obj_invoice = self.env['account.invoice'].browse(
            self.env.context['active_id'])
        obj_cce = self.env['l10n_br_account.invoice.cce']

        for invoice in obj_invoice:
            chave_nfe = invoice.nfe_access_key

            event_obj = self.env['l10n_br_account.document_event']
            domain = [('invoice_id', '=', invoice.id)]
            sequencia = len(obj_cce.search(domain)) + 1
            results = []
            try:
                processo = send_correction_letter(
                    invoice.company_id,
                    chave_nfe,
                    sequencia,
                    correcao)
                vals = {
                    'type': str(processo.webservice),
                    'status': processo.resposta.retEvento[0].infEvento.
                    cStat.valor,
                    'response': '',
                    'company_id': invoice.company_id.id,
                    'origin': '[CC-E] ' + str(invoice.fiscal_number),
                    'message': processo.resposta.retEvento[0].infEvento.
                    xEvento.valor,
                    'state': 'done',
                    'document_event_ids': invoice.id}
                results.append(vals)
                obj_invoice.attach_file_event(
                    sequencia,
                    'cce',
                    'xml')

            except Exception as e:
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': invoice.company_id.id,
                    'origin': '[CC-E]' + str(invoice.fiscal_number),
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + e.message,
                    'state': 'done',
                    'document_event_ids': invoice.id,
                }
                results.append(vals)
            finally:
                for result in results:
                    event_obj.create(result)
                    obj_cce.create({'invoice_id': invoice.id,
                                    'motivo': correcao,
                                    'sequencia': sequencia,
                                    })
        return {'type': 'ir.actions.act_window_close'}
