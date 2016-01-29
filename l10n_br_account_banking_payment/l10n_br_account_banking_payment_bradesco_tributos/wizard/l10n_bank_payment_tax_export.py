# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Luiz Felipe do Divino
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
from ..bradesco.bradesco_tax import BradescoGnre


class L10nPaymentTax(models.TransientModel):
    _name = 'payment.tax'
    _description = 'Export payment tax order'

    tax_file = fields.Binary('Send File', readonly=True)
    state = fields.Selection(
        [('init', 'init'),
         ('done', 'done')],
        'state',
        default='init',
        readonly=True)

    @api.multi
    def export(self):
        order_id = self.env.context.get('active_ids', [])[0]

        # TODO: Corrigir lista retornando dentro do FOR
        order = self.env['payment.order'].browse(order_id)
        gnre = BradescoGnre()
        remessa = gnre.remessa(order)
        self.state = 'done'
        self.tax_file = base64.b64encode(remessa)
        workflow.trg_validate(self.env.uid, 'payment.order', order_id, 'done',
                              self.env.cr)

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
