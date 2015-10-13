# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
            result[company.id] = {'product_tax_ids': []}
            product_tax_ids = [tax.tax_id.id for tax in
                               company.product_tax_definition_line]
            product_tax_ids.sort()
            result[company.id]['product_tax_ids'] = product_tax_ids
        return result

    _columns = {
        'product_invoice_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal'),
        'document_serie_product_ids': fields.many2many(
            'l10n_br_account.document.serie',
            'res_company_l10n_br_account_document_serie', 'company_id',
            'document_serie_product_id', 'Série de Documentos Fiscais',
            domain="[('company_id', '=', active_id),('active','=',True),"
            "('fiscal_type','=','product')]"),
        'nfe_version': fields.selection(
            [('1.10', '1.10'), ('2.00', '2.00'), ('3.10', '3.10')], 'Versão NFe', required=True),
        'nfe_import_folder': fields.char('Pasta de Importação', size=254),
        'nfe_export_folder': fields.char('Pasta de Exportação', size=254),
        'nfe_backup_folder': fields.char('Pasta de Backup', size=254),
        'nfe_environment': fields.selection(
            [('1', u'Produção'), ('2', u'Homologação')], 'Ambiente Padrão'),
        'file_type': fields.selection(
            [('xml', 'XML'), ('txt', ' TXT')], 'Tipo do Arquivo Padrão'),
        'sign_xml': fields.boolean('Assinar XML'),
        'export_folder': fields.boolean(u'Salvar na Pasta de Exportação'),
        'product_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.company.product',
            'company_id', 'Taxes Definitions'),
        'product_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
        'in_invoice_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal de Produto Padrão de Entrada',
            domain="[('journal_type','=','purchase'),"
            " ('state', '=', 'approved'), ('fiscal_type','=','product'),"
            " ('type','=','input')]"),
        'out_invoice_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal de Produto Padrão de Saida',
            domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
            " ('fiscal_type','=','product'), ('type','=','output')]"),
        'in_refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Devolução Entrada',
            domain="[('journal_type','=','purchase_refund'),"
            "('state', '=', 'approved'), ('fiscal_type','=','product'),"
            "('type','=','output')]"),
        'out_refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Devolução Saida',
            domain="[('journal_type','=','sale_refund'),"
            "('state', '=', 'approved'), ('fiscal_type','=','product'),"
            " ('type','=','input')]"),
        'nfe_a1_file': fields.binary('Arquivo NFe A1'),
        'nfe_a1_password': fields.char('Senha NFe A1', size=64)
    }
    _defaults = {
        'nfe_version': '2.00',
    }


class L10n_brTaxDefinitionCompanyProduct(orm.Model):
    _name = 'l10n_br_tax.definition.company.product'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
        'company_id': fields.many2one('res.company', 'Empresa', select=True),
    }
    _sql_constraints = SQL_CONSTRAINTS