# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 Luiz Felipe do Divino - KMEE - www.kmee.com.br           #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api, _
import os
import base64
import time


class NfeXmlPeriodicExport(models.TransientModel):
    _inherit = 'nfe.xml.periodic.export'

    zip_sat_file = fields.Binary('Zip SAT', readonly=True)

    @api.multi
    def export(self):
        if self.start_period_id.company_id.parent_id.id:
            pos_order_model = self.env['pos.order']
            pos_orders = pos_order_model.search([
                ('date_order', '>=', self.start_period_id.date_start),
                ('date_order', '<=', self.stop_period_id.date_stop),
            ])
        else:
            pos_order_model = self.env['pos.order']
            pos_orders = pos_order_model.search([
                ('date_order', '>=', self.start_period_id.date_start),
                ('date_order', '<=', self.stop_period_id.date_stop),
                ('company_id', '=', self.create_uid.company_id.id),
            ])

        if pos_orders:
            caminhos_xmls = ''
            for pos_order in pos_orders:
                fp_new = open(
                    self.start_period_id.company_id.nfe_root_folder
                    + pos_order.chave_cfe + '.xml', 'w'
                )
                fp_new.write(base64.b64decode(pos_order.cfe_return))
                fp_new.close()

                caminhos_xmls += self.start_period_id\
                                     .company_id.nfe_root_folder + pos_order\
                    .chave_cfe + '.xml '

            os.system(
                "zip -r " + os.path.join(
                    self.start_period_id.company_id.nfe_root_folder,
                    'cfes_xmls_' + time.strftime("%Y-%m-%d"))
                + ' ' + caminhos_xmls
            )

            for pos_order in pos_orders:
                os.remove(
                    self.start_period_id.company_id.nfe_root_folder
                    + pos_order.chave_cfe + '.xml'
                )

        orderFile = open(
            os.path.join(
                self.start_period_id.company_id.nfe_root_folder,
                'cfes_xmls_' + time.strftime("%Y-%m-%d") + '.zip'
            ), 'r'
        )
        itemFile = orderFile.read()

        self.write({
            'state': 'done',
            'zip_sat_file': base64.b64encode(itemFile),
            'name': 'cfes_xmls_' + time.strftime("%Y-%m-%d") + '.zip',
        })

        return super(NfeXmlPeriodicExport, self).export()
