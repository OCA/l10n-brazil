# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
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
#                                                                             #
###############################################################################


from odoo import api, fields, models


class WizardNfeImport(models.TransientModel):
    _inherit = 'nfe_import.account_invoice_import'

    nfe_mde_id = fields.Many2one(
        'nfe.mde', u"Xml de Manifesto",
        domain="[('partner_id', '=', supplier_partner_id), \
            ('xml_downloaded', '=', True), ('xml_imported', '=', False)]")

    @api.multi
    def import_edoc(self):
        if self.nfe_mde_id:
            attach_xml = self.env['ir.attachment'].search([
                ('res_id', '=', self.nfe_mde_id.id),
                ('res_model', '=', 'nfe.mde'),
                ('name', '=like', 'NFe%')
            ], limit=1)

            if attach_xml:
                self.edoc_input = attach_xml.datas
                self.file_name = attach_xml.datas_fname
            elif not self.edoc_input:
                raise Warning(
                    u'Atenção!',
                    u'Selecione o xml ou manifesto para realizar a importação')

        return super(WizardNfeImport, self).import_edoc()
