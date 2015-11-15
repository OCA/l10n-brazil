# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api


class L10nBrAccountNfeExport(models.TransientModel):
    """ Exportar Nota Fiscal Eletrônica """
    _name = 'l10n_br_account_product.nfe_export'
    _inherit = 'l10n_br_account_product.nfe_export_invoice'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_account_product.nfe_export'))
    import_status_draft = fields.Boolean(
        string="Importar NFs com status em rascunho")
    nfe_export_result = fields.One2many(
        comodel_name='l10n_br_account_product.nfe_export_result',
        inverse_name='wizard_id',
        string='NFe Export Result')

    @api.multi
    def _get_invoice_ids(self):
        return self.env['account.invoice'].search([
            ('state', '=', 'sefaz_export'),
            ('nfe_export_date', '=', False),
            ('company_id', '=', self.company_id.id),
            ('issuer', '=', '0')])


class L10nBrAccountNfeExportResult(models.TransientModel):
    _name = 'l10n_br_account_product.nfe_export_result'
    _inherit = 'l10n_br_account_product.nfe_export_invoice_result'

    wizard_id = fields.Many2one(
        comodel_name='l10n_br_account_product.nfe_export',
        string='Wizard ID',
        ondelete='cascade',
        select=True)
