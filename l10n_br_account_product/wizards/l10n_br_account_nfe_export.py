# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class L10nBrAccountNfeExport(models.TransientModel):
    """ Exportar Nota Fiscal Eletrônica """
    _name = 'l10n_br_account_product.nfe_export'
    _inherit = 'l10n_br_account_product.nfe_export_invoice'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.user.company_id)

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
        ondelete='cascade')
