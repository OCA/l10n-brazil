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

from openerp.addons.l10n_br_account.models.l10n_br_account import (
    L10nBrTaxDefinition
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.one
    @api.depends('service_tax_definition_line.tax_id')
    def _compute_service_taxes(self):
        service_taxes = self.env['account.tax']
        for tax in self.service_tax_definition_line:
            service_taxes += tax.tax_id
        self.product_tax_ids = service_taxes

    service_invoice_id = fields.Many2one(
        'l10n_br_account.fiscal.document',
        'Documento Fiscal')
    document_serie_service_id = fields.Many2one(
        'l10n_br_account.document.serie', u'Série Fiscais para Serviço',
        domain="[('company_id', '=', active_id),('active','=',True),"
        "('fiscal_type','=','service')]")
    nfse_version = fields.Selection(
        [('100', '1.00')], 'Versão NFse', required=True, default="100")
    nfse_import_folder = fields.Char('Pasta de Origem', size=254)
    nfse_export_folder = fields.Char('Pasta de Destino', size=254)
    nfse_backup_folder = fields.Char('Pasta de Backup', size=254)
    service_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.company.service',
        'company_id', 'Taxes Definitions')
    service_tax_ids = fields.Many2many('account.tax',
                                       string='Service Taxes',
                                       compute='_compute_service_taxes',
                                       store=True)
    in_invoice_service_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal Padrão de Aquisição de Serviço',
        domain="[('journal_type','=','purchase'), "
        " ('fiscal_type','=','service'), ('type','=','input'),"
        " ('state', '=', 'approved')]")
    out_invoice_service_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Categoria Fiscal Padrão de Prestação de Serviço',
        domain="""[('journal_type','=','sale'),
        ('fiscal_type','=','service'), ('type','=','output'),
        ('state', '=', 'approved')]""")


class L10nbrTaxDefinitionCompanyService(L10nBrTaxDefinition, models.Model):
    _name = 'l10n_br_tax.definition.company.service'
