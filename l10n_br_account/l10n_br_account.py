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


class l10n_br_account_cfop(osv.osv):
    """ CFOP - Código Fiscal de Operações e Prestações """
    _name = 'l10n_br_account.cfop'
    _description = 'CFOP'
    _columns = {
        'code': fields.char('Código', size=4, requeried=True),
        'name': fields.char('Nome', size=256, requeried=True),
        'small_name': fields.char('Nome Reduzido', size=32, requeried=True),
        'description': fields.text('Descrição'),
        'type': fields.selection([('input', 'Entrada'),
                                  ('output', 'Saida')],
                                 'Tipo', requeried=True),
        'parent_id': fields.many2one('l10n_br_account.cfop', 'CFOP Pai'),
        'child_ids': fields.one2many('l10n_br_account.cfop',
                                     'parent_id',
                                     'CFOP Filhos'),
        'internal_type': fields.selection([('view', 'Visualização'),
                                           ('normal', 'Normal')],
                                          'Tipo Interno',
                                          required=True)}
    _defaults = {
        'internal_type': 'normal'}

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=80):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = self.search(cr, user, ['|', ('name', operator, name),
                                     ('code', operator, name)] + args,
                          limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context,
                          load='_classic_write')
        return [(x['id'], (x['code'] and x['code'] or '') +
                 (x['name'] and ' - ' + x['name'] or '')) for x in reads]

l10n_br_account_cfop()


class l10n_br_account_service_type(osv.osv):
    _name = 'l10n_br_account.service.type'
    _description = 'Cadastro de Operações Fiscais de Serviço'
    _columns = {
        'code': fields.char('Código', size=16, required=True),
        'name': fields.char('Descrição', size=256, required=True),
        'parent_id': fields.many2one('l10n_br_account.service.type',
                                     'Tipo de Serviço Pai'),
        'child_ids': fields.one2many('l10n_br_account.service.type',
                                     'parent_id',
                                     'Tipo de Serviço Filhos'),
        'country_id': fields.many2one('res.country', 'País'),
        'state_id': fields.many2one('res.country.state', 'Estado'),
        'l10n_br_city_id': fields.many2one('l10n_br_base.city', 'Município'),
        'internal_type': fields.selection([('view', 'Visualização'),
                                           ('normal', 'Normal')],
                                          'Tipo Interno',
                                          required=True)}
    _defaults = {
        'internal_type': 'normal'}

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res

l10n_br_account_service_type()


class l10n_br_account_fiscal_document(osv.osv):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'
    _columns = {
        'code': fields.char(u'Codigo', size=8, required=True),
        'name': fields.char(u'Descrição', size=64),
        'electronic': fields.boolean(u'Eletrônico')}

l10n_br_account_fiscal_document()


class l10n_br_account_fiscal_category(osv.osv):
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscail'
    _columns = {
        'code': fields.char('Código', size=254, required=True),
        'name': fields.char('Descrição', size=254),
        'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')],
                                 'Tipo'),
        'property_journal': fields.property('account.journal',
                                            type='many2one',
                                            relation='account.journal',
                                            string="Diário Contábil",
                                            method=True,
                                            view_load=True,
                                            help="Diário utilizado para esta"
                                            "categoria de operação fiscal"),
        'fiscal_type': fields.selection([('product', 'Produto'),
                                         ('service', 'Serviço')],
                                        'Tipo Fiscal', requeried=True),
        'journal_type': fields.selection(
            [('sale', 'Venda'),
             ('sale_refund','Devolução de Venda'),
             ('purchase', 'Compras'),
             ('purchase_refund','Devolução de Compras')], 'Tipo do Diário',
            size=32, required=True),
        'refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria Fiscal de Devolução',
            domain="[('type', '!=', type), ('fiscal_type', '=', fiscal_type), \
            ('journal_type', 'like', journal_type)]"),
        'fiscal_position_ids': fields.one2many('account.fiscal.position',
                                               'fiscal_category_id',
                                               'Fiscal Positions'),
        'note': fields.text(u'Observações')}
    _defaults = {
        'type': 'output',
        'fiscal_type': 'product',
        'journal_type': 'sale'}

l10n_br_account_fiscal_category()


class l10n_br_account_document_serie(osv.osv):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'
    _columns = {
        'code': fields.char('Código', size=3, required=True),
        'name': fields.char('Descrição', size=64, required=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal', required=True),
        'company_id': fields.many2one('res.company', 'Company',
                                      required=True),
        'active': fields.boolean('Active'),
        'fiscal_type': fields.selection([('product', 'Product'),
                                         ('service', 'Service')],
                                        'Tipo Fiscal', required=True),
        'internal_sequence_id': fields.many2one('ir.sequence',
                                                'Sequência Interna')}
    _defaults = {
        'active': True,
        'fiscal_type': 'product'}

    def create_sequence(self, cr, uid, vals, context=None):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def create(self, cr, uid, vals, context=None):
        """ Overwrite method to create a new ir.sequence if 
         this field is null """
        if not 'internal_sequence_id' in vals or not vals['internal_sequence_id']:
            vals.update({'internal_sequence_id': self.create_sequence(cr, uid, vals, context)})
        return super(l10n_br_account_document_serie, self).create(cr, uid, vals, context)

l10n_br_account_document_serie()


class l10n_br_account_partner_fiscal_type(osv.osv):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'
    _columns = {
        'code': fields.char('Código', size=16, required=True),
        'name': fields.char('Descrição', size=64),
        'tipo_pessoa': fields.selection([('F', 'Física'), ('J', 'Jurídica')],
                                        'Tipo de pessoa', required=True),
        'icms': fields.boolean('Recupera ICMS'),
        'ipi': fields.boolean('Recupera IPI')}

l10n_br_account_partner_fiscal_type()


class l10n_br_account_cnae(osv.osv):
    _name = 'l10n_br_account.cnae'
    _description = 'Cadastro de CNAE'
    _columns = {
        'code': fields.char('Código', size=16, required=True),
        'name': fields.char('Descrição', size=64, required=True),
        'version': fields.char('Versão', size=16, required=True),
        'parent_id': fields.many2one('l10n_br_account.cnae', 'CNAE Pai'),
        'child_ids': fields.one2many('l10n_br_account.cnae',
                                     'parent_id', 'CNAEs Filhos'),
        'internal_type': fields.selection([('view', 'Visualização'),
                                           ('normal', 'Normal')],
                                          'Tipo Interno',
                                          required=True)}
    _defaults = {
        'internal_type': 'normal'}

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res

l10n_br_account_cnae()


class l10n_br_tax_definition_template(osv.osv):
    _name = 'l10n_br_tax.definition.template'
    _columns = {
        'tax_id': fields.many2one('account.tax.template', 'Imposto',
                                  required=True),
        'tax_domain': fields.related('tax_id', 'domain',
                                     type='char'),
        'tax_code_id': fields.many2one('account.tax.code.template',
                                       'Código de Imposto')}
    
    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}

l10n_br_tax_definition_template()


class l10n_br_tax_definition(osv.osv):
    _name = 'l10n_br_tax.definition'
    _columns = {
        'tax_id': fields.many2one('account.tax', 'Imposto', required=True),
        'tax_domain': fields.related('tax_id', 'domain',
                                     type='char'),
        'tax_code_id': fields.many2one('account.tax.code',
                                       'Código de Imposto'),
        'company_id': fields.related(
            'tax_id', 'company_id', type='many2one', readonly=True,
            relation='res.company', store=True,
            string='Company')}
    
    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}

l10n_br_tax_definition()
