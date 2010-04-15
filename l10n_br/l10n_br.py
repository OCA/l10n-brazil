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
# Municipios e Códigos do IBGE
#################################################################################
class l10n_br_city(osv.osv):
    _name = 'l10n_br.city'
    _description = 'Municipios e Códigos do IBGE'
    _columns = {
        'name': fields.char('Nome', size=64, required=True),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'ibge_code': fields.char('Codigo IBGE', size=7),
    }
l10n_br_city()

#################################################################################
# CEP - Código de endereçamento Postal
#################################################################################
class l10n_br_cep(osv.osv):
    _name = 'l10n_br.cep'
    _rec_name = 'code'
    _columns = {
        'code': fields.char('CEP', size=8, required=True),
        'street_type': fields.char('Tipo', size=26),
        'street': fields.char('Logradouro', size=72),
        'district': fields.char('Bairro', size=72),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'city_id': fields.many2one('l10n_br.city', 'Cidade', required=True, domain="[('state_id','=',state_id)]"),
    }
l10n_br_cep()

#################################################################################
# CFOP - Código Fiscal de Operações e Prestações
#################################################################################
class l10n_br_cfop(osv.osv):
    _description = 'CFOP - Código Fiscal de Operações e Prestações'
    _name = 'l10n_br.cfop'
    
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
        'parent_id': fields.many2one('l10n_br.cfop', 'CFOP Pai'),
        'child_ids': fields.one2many('l10n_br.cfop', 'parent_id', 'CFOP filhos'),
    }
l10n_br_cfop()

#################################################################################
# Tipo de Documento Fiscal
#################################################################################
class l10n_br_fiscal_document(osv.osv):
    _name = 'l10n_br.fiscal.document'
    _description = 'Tipo de Documento Fiscal'
    _columns = {
        'code': fields.char('Codigo', size=8),
        'name': fields.char('Descrição', size=64),
        'nfe': fields.boolean('NFe'),
    }
l10n_br_fiscal_document()

#################################################################################
# Código de Situação Tributária
#################################################################################
class l10n_br_cst(osv.osv):
    _name = 'l10n_br.cst'
    _description = 'Código de Situação Tributária'
    _columns = {
        'code': fields.char('Codigo', size=8,required=True),
        'name': fields.char('Descrição', size=64),
        'tax_code_id': fields.many2one('account.tax.code.template', 'Modelo do Imposto',required=True),
    }
l10n_br_cst()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
