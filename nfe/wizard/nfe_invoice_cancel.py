# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Rafael da Silva Lima - KMEE, www.kmee.com.br
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

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
