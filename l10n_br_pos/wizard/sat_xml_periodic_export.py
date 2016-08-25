# -*- encoding: utf-8 -*-

# Copyright (C) 2016 Luiz Felipe do Divino - KMEE - www.kmee.com.br           #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
import os
import base64
import time


class NfeXmlPeriodicExport(models.TransientModel):
    _inherit = 'nfe.xml.periodic.export'

    zip_sat_file = fields.Binary('Zip SAT', readonly=True)

    @api.multi
    def export(self):
        if not self.create_uid.company_id.parent_id.id:
            pos_order_model = self.env['pos.order']
            pos_orders = pos_order_model.search([
                ('date_order', '>=', self.start_period_id.date_start),
                ('date_order', '<=', self.stop_period_id.date_stop),
                ('cfe_return', '!=', False),
            ])
        else:
            pos_order_model = self.env['pos.order']
            pos_orders = pos_order_model.search([
                ('date_order', '>=', self.start_period_id.date_start),
                ('date_order', '<=', self.stop_period_id.date_stop),
                ('company_id', '=', self.create_uid.company_id.id),
                ('cfe_return', '!=', False),
            ])

        if pos_orders:
            caminhos_xmls = ''
            for pos_order in pos_orders:
                fp_new = open(
                    self.create_uid.company_id.nfe_root_folder
                    + pos_order.chave_cfe + '.xml', 'w'
                )
                fp_new.write(base64.b64decode(pos_order.cfe_return))
                fp_new.close()

                caminhos_xmls += self.create_uid.company_id.nfe_root_folder + pos_order.chave_cfe + '.xml '

                if pos_order.cfe_cancelamento_return:
                    fp_new = open(
                        self.create_uid.company_id.nfe_root_folder
                        + pos_order.chave_cfe_cancelamento + '.xml', 'w'
                    )
                    fp_new.write(base64.b64decode(
                        pos_order.cfe_cancelamento_return
                    ))
                    fp_new.close()

                    caminhos_xmls += self.create_uid.company_id.nfe_root_folder + pos_order.chave_cfe_cancelamento + '.xml '

            if not self.create_uid.company_id.parent_id.id:
                os.system(
                    "zip -r " + os.path.join(
                        self.create_uid.company_id.nfe_root_folder,
                        'cfes_xmls_' + time.strftime("%Y-%m-%d"))
                    + ' ' + caminhos_xmls
                )
            else:
                os.system(
                    "zip -r " + os.path.join(
                        self.create_uid.company_id.nfe_root_folder,
                        'cfes_xmls_' + self.create_uid.company_id.name.replace(
                            " ", "") + "_" + time.strftime("%Y-%m-%d"))
                    + ' ' + caminhos_xmls
                )

            for pos_order in pos_orders:
                os.remove(
                    self.create_uid.company_id.nfe_root_folder
                    + pos_order.chave_cfe + '.xml'
                )

        if not self.create_uid.company_id.parent_id.id:
            orderFile = open(
                os.path.join(
                    self.create_uid.company_id.nfe_root_folder,
                    'cfes_xmls_' + time.strftime("%Y-%m-%d") + '.zip'
                ), 'r'
            )
        else:
            orderFile = open(
                os.path.join(
                    self.create_uid.company_id.nfe_root_folder,
                    'cfes_xmls_' + self.create_uid.company_id.name.replace(
                        " ", "") + "_" + time.strftime("%Y-%m-%d") + '.zip'
                ), 'r'
            )

        itemFile = orderFile.read()

        if not self.create_uid.company_id.parent_id.id:
            self.write({
                'state': 'done',
                'zip_sat_file': base64.b64encode(itemFile),
                'name': 'cfes_xmls_' + time.strftime("%Y-%m-%d") + '.zip',
            })
        else:
            self.write({
                'state': 'done',
                'zip_sat_file': base64.b64encode(itemFile),
                'name': 'cfes_xmls_' + self.create_uid.company_id.name.replace(
                        " ", "") + "_" + time.strftime("%Y-%m-%d") + '.zip',
            })

        return super(NfeXmlPeriodicExport, self).export()
