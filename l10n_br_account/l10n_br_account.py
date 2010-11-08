# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields

#################################################################################
# CFOP - Código Fiscal de Operações e Prestações
#################################################################################
class l10n_br_account_cfop(osv.osv):
    _description = 'CFOP - Código Fiscal de Operações e Prestações'
    _name = 'l10n_br_account.cfop'
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = self.search(cr, user, ['|',('name',operator,name),('code',operator,name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','code'], context, load='_classic_write')
        return [(x['id'], (x['code'] and x['code'] + ' - ' or '') + x['name']) \
                for x in reads]
            
    _columns = {
        'code': fields.char('Código', size=4),
        'name': fields.char('Nome', size=256),
        'small_name': fields.char('Nome Reduzido', size=32),
        'description': fields.text('Descrição'),
        'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')], 'Tipo'),
        'parent_id': fields.many2one('l10n_br_account.cfop', 'CFOP Pai'),
        'child_ids': fields.one2many('l10n_br_account.cfop', 'parent_id', 'CFOP filhos'),
    }
l10n_br_account_cfop()

#################################################################################
# Tipo de Documento Fiscal
#################################################################################
class l10n_br_account_fiscal_document(osv.osv):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'
    _columns = {
        'code': fields.char('Codigo', size=8),
        'name': fields.char('Descrição', size=64),
        'nfe': fields.boolean('NFe'),
    }
l10n_br_account_fiscal_document()

#################################################################################
# Código de Situação Tributária
#################################################################################
class l10n_br_account_cst(osv.osv):
    _name = 'l10n_br_account.cst'
    _description = 'Código de Situação Tributária'
    _columns = {
        'code': fields.char('Codigo', size=8,required=True),
        'name': fields.char('Descrição', size=64),
        'tax_code_id': fields.many2one('account.tax.code', 'Modelo do Imposto',required=True),
    }
l10n_br_account_cst()

#################################################################################
# Categorias Operações Fiscais
#################################################################################
class l10n_br_account_fiscal_operation_category(osv.osv):
    _name = 'l10n_br_account.fiscal.operation.category'
    _description = 'Categoria de Operações Fiscais'
    _columns = {
                'code': fields.char('Código', size=24, required=True),
                'name': fields.char('Descrição', size=64),
                'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')], 'Tipo'),
                'use_sale' : fields.boolean('Usado em Vendas'),
                'use_invoice' : fields.boolean('Usado nas Notas Fiscais'),
                'use_purchase' : fields.boolean('Usado nas Compras'),
                'use_picking' : fields.boolean('Usado nas Listas de Separações'),
                }
    _defaults = {
        'type': 'output',
    }
l10n_br_account_fiscal_operation_category()

#################################################################################
# Operações Fiscais
#################################################################################
class l10n_br_account_fiscal_operation(osv.osv):
    _name = 'l10n_br_account.fiscal.operation'
    _description = 'Operações fiscais'
    _columns = {
                'code': fields.char('Código', size=16, required=True),
                'name': fields.char('Descrição', size=64),
                'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')], 'Tipo', requeried=True),
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', domain="[('type','=',type)]", requeried=True),
                'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP', requeried=True),
                'fiscal_document_id': fields.many2one('l10n_br_account.fiscal.document', 'Documento Fiscal', requeried=True),
                'fiscal_operation_line': fields.one2many('l10n_br_account.fiscal.operation.line', 'fiscal_operation_id', 'Fiscal Operation Lines'),
                'use_sale' : fields.boolean('Usado em Vendas'),
                'use_invoice' : fields.boolean('Usado nas Notas Fiscais'),
                'use_purchase' : fields.boolean('Usado nas Compras'),
                'use_picking' : fields.boolean('Usado nas Listas de Separações'),
                }
    _defaults = {
        'type': 'output',
    }

l10n_br_account_fiscal_operation()

#################################################################################
# Linhas das Operações fiscais
#################################################################################
class l10n_br_account_fiscal_operation_line(osv.osv):
    _name = 'l10n_br_account.fiscal.operation.line'
    _description = 'Linhas das operações ficais'
    _columns = {
                'tax_code_id': fields.many2one('account.tax.code', 'Código do Imposto'),
                'cst_id': fields.many2one('l10n_br_account.cst', 'Código de Situação Tributária'),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Fiscal Operation Ref', ondelete='cascade', select=True),
               }

l10n_br_account_fiscal_operation_line()

#################################################################################
# Serie de Documentos Fiscais
#################################################################################
class l10n_br_account_document_serie(osv.osv):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'
    _columns = {
                'code': fields.char('Código', size=3, required=True),
                'name': fields.char('Descrição', size=64),
                'fiscal_document_id': fields.many2one('l10n_br_account.fiscal.document', 'Documento Fiscal', requeried=True),
                'company_id': fields.many2one('res.company', 'Empresa', requeried=True),
                'active':fields.boolean('Ativo'),
                }

l10n_br_account_document_serie()

################################################################################
# Tipo Fiscal de Parceiros
#################################################################################
class l10n_br_account_partner_fiscal_type(osv.osv):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'
    _columns = {
                'code': fields.char('Código', size=16, required=True),
                'name': fields.char('Descrição', size=64),
                'tipo_pessoa': fields.selection([('F', 'Física'), ('J', 'Jurídica')], 'Tipo de pessoa', required=True),
                'icms': fields.boolean('Recupera ICMS'),
                'ipi':fields.boolean('Recupera IPI'), 
                }

l10n_br_account_partner_fiscal_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
