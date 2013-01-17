# -*- encoding: utf-8 -*-
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

from osv import osv, fields
import decimal_precision as dp


class res_company(osv.osv):
    _inherit = 'res.company'
    
    def _get_taxes(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for company in self.browse(cr, uid, ids, context=context):
            result[company.id] = {'product_tax_ids': [],
                                  'service_tax_ids': []}
            product_tax_ids = [tax.tax_id.id for tax in 
                               company.product_tax_definition_line]
            service_tax_ids = [tax.tax_id.id for tax in 
                               company.service_tax_definition_line]
            product_tax_ids.sort()
            service_tax_ids.sort()
            result[company.id]['product_tax_ids'] = product_tax_ids
            result[company.id]['service_tax_ids'] = service_tax_ids
        return result
    
    _columns = {
        'fiscal_type': fields.selection([
            ('1', 'Simples Nacional'),
            ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
            ('3', 'Regime Normal')],
            'Regime Tributário', required=True),
        'annual_revenue': fields.float(
            'Faturamento Anual', required=True,
            digits_compute=dp.get_precision('Account'),
            help="Faturamento Bruto dos últimos 12 meses"),
        'product_invoice_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal'),
        'service_invoice_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal'),
        'document_serie_product_ids': fields.many2many(
            'l10n_br_account.document.serie',
            'res_company_l10n_br_account_document_serie', 'company_id',
            'document_serie_product_id', 'Série de Documentos Fiscais',
            domain="[('company_id', '=', active_id),('active','=',True),"
            "('fiscal_type','=','product')]"),
        'document_serie_service_id': fields.many2one(
            'l10n_br_account.document.serie', 'Série Fiscais para Serviço',
            domain="[('company_id', '=', active_id),('active','=',True),"
            "('fiscal_type','=','service')]"),
        'cnae_main_id': fields.many2one('l10n_br_account.cnae',
                                        'CNAE Primário'),
        'cnae_secondary_ids': fields.many2many(
            'l10n_br_account.cnae',
            'res_company_l10n_br_account_cnae',
            'company_id', 'cnae_id',
            'CNAE Segundários'),
        'nfe_version': fields.selection([('110', '1.10'),
                                         ('200', '2.00')], 'Versão NFe',
                                        required=True),
        'nfe_import_folder': fields.char('Pasta de Importação', size=254),
        'nfe_export_folder': fields.char('Pasta de Exportação', size=254),
        'nfe_backup_folder': fields.char('Pasta de Backup', size=254),
        'nfse_version': fields.selection([('100', '1.00')], 'Versão NFse',
                                         required=True),
        'nfse_import_folder': fields.char('Pasta de Origem', size=254),
        'nfse_export_folder': fields.char('Pasta de Destino', size=254),
        'nfse_backup_folder': fields.char('Pasta de Backup', size=254),
        'product_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.company.product',
            'company_id', 'Taxes Definitions'),
        'product_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
        'service_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.company.service',
            'company_id', 'Taxes Definitions'),
        'service_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
        'in_invoice_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal de Produto Padrão de Entrada',
            domain="[('journal_type','=','purchase'), ('fiscal_type','=','product'),"
            " ('type','=','input')]"),
        'out_invoice_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal de Produto Padrão de Saida',
            domain="[('journal_type','=','sale'), ('fiscal_type','=','product'),"
            " ('type','=','output')]"),
        'in_refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Devolução Entrada',
            domain="[('journal_type','=','purchase_refund'), ('fiscal_type','=','product'),"
            " ('type','=','output')]"),
        'out_refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Devolução Saida',
            domain="[('journal_type','=','sale_refund'), ('fiscal_type','=','product'),"
            " ('type','=','input')]"),
        'in_invoice_service_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal Padrão de Aquisição de Serviço',
            domain="[('journal_type','=','purchase'), ('fiscal_type','=','service'),"
            " ('type','=','input')]"),
        'out_invoice_service_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal Padrão de Prestação de Serviço',
            domain="[('journal_type','=','sale'), ('fiscal_type','=','service'),"
            " ('type','=','output')]"),
        'ecnpj_a1_file': fields.binary('Arquivo e-CNPJ A1'),
        'ecnpj_a1_password': fields.char('Senha e-CNPJ A1', size=64),
        'nfe_a1_file': fields.binary('Arquivo NFe A1'),
        'nfe_a1_password': fields.char('Senha NFe A1', size=64)
    }
    _defaults = {
        'fiscal_type': '3',
        'nfe_version': '200',
        'nfse_version': '110',
        'annual_revenue': 0.0}

res_company()


class l10n_br_tax_definition_company_product(osv.osv):
    _name = 'l10n_br_tax.definition.company.product'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
                'company_id': fields.many2one(
                    'res.company', 'Company', select=True)}
    
    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        company_id)',
        u'Imposto já existente nesta empresa!')]

l10n_br_tax_definition_company_product()


class l10n_br_tax_definition_company_service(osv.osv):
    _name = 'l10n_br_tax.definition.company.service'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
                'company_id': fields.many2one(
                    'res.company', 'Company', select=True)}
    
    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        company_id)',
        u'Imposto já existente nesta empresa!')]

l10n_br_tax_definition_company_service()
