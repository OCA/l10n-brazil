# -*- coding: utf-8 -*-
# Copyright (C) 2016 Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


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
