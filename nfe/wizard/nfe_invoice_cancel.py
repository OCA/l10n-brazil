# -*- coding: utf-8 -*-
# Copyright (C) 2014  Rafael da Silva Lima - KMEE, www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class NfeInvoiceCancel(models.Model):
    _name = 'nfe.invoice_cancel'

    justificativa = fields.Text('Justificativa', size=255, required=True)

    @api.multi
    def _check_name(self):
        for nfe in self:
            if not (len(nfe.justificativa) >= 15):
                return False
        return True

    _constraints = [
        (_check_name,
         'Tamanho de justificativa inválida !',
         ['justificativa'])]

    @api.multi
    def action_enviar_cancelamento(self):

        for cancel in self:
            obj_invoice = self.env['account.invoice'].browse(
                self.env.context['active_id'])
            obj_invoice.cancel_invoice_online(cancel.justificativa)
        return {'type': 'ir.actions.act_window_close'}
