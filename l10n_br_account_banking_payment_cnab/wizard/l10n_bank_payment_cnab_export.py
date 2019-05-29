# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, workflow, fields
import base64
import time
from ..febraban.cnab import Cnab

# TODO Server action para a cada dia retornar o sufixo do arquivo para zero


class L10nPaymentCnab(models.TransientModel):
    _name = 'payment.cnab'
    _description = 'Export payment order(s) in cnab layout'

    name = fields.Char(u'Nome', size=255)
    cnab_file = fields.Binary('CNAB File', readonly=True)
    state = fields.Selection(
        [('init', 'init'),
         ('done', 'done')],
        'state',
        default='init',
        readonly=True)

    @api.multi
    def export(self):
        for order_id in self.env.context.get('active_ids', []):

            order = self.env['payment.order'].browse(order_id)
            cnab = Cnab.get_cnab(order.mode.bank_id.bank_bic,
                                 order.mode.type.code)()
            remessa = cnab.remessa(order)
            suf_arquivo = order.get_next_sufixo()

            if order.mode.type.code == '240':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            elif order.mode.type.code == '400':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(suf_arquivo))
            elif order.mode.type.code == '500':
                self.name = 'PG%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            self.state = 'done'
            self.cnab_file = base64.b64encode(remessa)
            workflow.trg_validate(self.env.uid, 'payment.order', order_id,
                                  'done', self.env.cr)

            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    @api.multi
    def done(self):
        return {'type': 'ir.actions.act_window_close'}
