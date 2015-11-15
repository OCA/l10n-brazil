# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm, fields

from openerp.addons.l10n_br_account.res_company import SQL_CONSTRAINTS


class ResCompany(orm.Model):
    _inherit = 'res.company'

    def _get_taxes(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for company in self.browse(cr, uid, ids, context=context):
            result[company.id] = {'service_tax_ids': []}
            service_tax_ids = [tax.tax_id.id for tax in
                               company.service_tax_definition_line]
            service_tax_ids.sort()
            result[company.id]['service_tax_ids'] = service_tax_ids
        return result

    _columns = {
        'nfse_version': fields.selection([('100', '1.00')], 'Versão NFse',
                                         required=True),
        'nfse_import_folder': fields.char('Pasta de Origem', size=254),
        'nfse_export_folder': fields.char('Pasta de Destino', size=254),
        'nfse_backup_folder': fields.char('Pasta de Backup', size=254),
        'service_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.company.service',
            'company_id', 'Taxes Definitions'),
        'service_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
        'in_invoice_service_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal Padrão de Aquisição de Serviço',
            domain="[('journal_type','=','purchase'), "
            " ('fiscal_type','=','service'), ('type','=','input'),"
            " ('state', '=', 'approved')]"),
        'out_invoice_service_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal Padrão de Prestação de Serviço',
            domain="""[('journal_type','=','sale'),
            ('fiscal_type','=','service'), ('type','=','output'),
            ('state', '=', 'approved')]"""),
    }
    _defaults = {
        'nfse_version': '100',
        'annual_revenue': 0.0
    }


class L10nBrTaxDefinitionCompanyService(orm.Model):
    _name = 'l10n_br_tax.definition.company.service'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', select=True),
    }
    _sql_constraints = SQL_CONSTRAINTS