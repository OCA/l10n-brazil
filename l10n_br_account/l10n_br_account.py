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


class l10n_br_account_fiscal_operation_category(osv.osv):
    _name = 'l10n_br_account.fiscal.operation.category'
    _description = 'Categoria de Operações Fiscais'
    _columns = {
        'code': fields.char('Código', size=24, required=True),
        'name': fields.char('Descrição', size=64),
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
        'use_sale': fields.boolean('Usado em Vendas'),
        'use_invoice': fields.boolean('Usado nas Notas Fiscais'),
        'use_purchase': fields.boolean('Usado nas Compras'),
        'use_picking': fields.boolean('Usado nas Listas de Separações')}
    _defaults = {
        'type': 'output',
        'fiscal_type': 'product'}

l10n_br_account_fiscal_operation_category()


class l10n_br_account_fiscal_operation(osv.osv):
    _name = 'l10n_br_account.fiscal.operation'
    _description = 'Operação Fiscais'
    _columns = {
        'code': fields.char('Código', size=16, required=True),
        'name': fields.char('Descrição', size=64),
        'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')],
                                 'Tipo', requeried=True),
        'fiscal_operation_category_id': fields.many2one(
            'l10n_br_account.fiscal.operation.category',
            'Categoria', domain="[('type','=',type)]",
            requeried=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal',
            requeried=True),
        'fiscal_operation_line': fields.one2many(
            'l10n_br_account.fiscal.operation.line',
            'fiscal_operation_id',
            'Fiscal Operation Lines'),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
        'service_type_id': fields.many2one('l10n_br_account.service.type',
                                           'Tipo de Serviço'),
        'use_sale': fields.boolean('Usado em Vendas'),
        'use_invoice': fields.boolean('Usado nas Notas Fiscais'),
        'use_purchase': fields.boolean('Usado nas Compras'),
        'use_picking': fields.boolean('Usado nas Listas de Separações'),
        'refund_fiscal_operation_id': fields.many2one(
            'l10n_br_account.fiscal.operation',
            'Op. Fiscal Devolução',
            domain="[('type','!=',type)]"),
        'note': fields.text('Observação'),
        'inv_copy_note': fields.boolean('Copiar Observação na Nota Fiscal'),
        'fiscal_type': fields.selection([('product', 'Produto'),
                                         ('service', 'Serviço')],
                                        'Tipo Fiscal',
                                        domain="[('fiscal_type','=',fiscal_type)]",
                                        requeried=True),
        'asset_operation': fields.boolean('Operação de Aquisição de Ativo',
                                          help="Caso seja marcada essa opção,"
                                          " será incluido o IPI na base de "
                                          "calculo do ICMS.")}
    _defaults = {
        'type': 'output',
        'fiscal_type': 'product',
        'fiscal_type': False}

l10n_br_account_fiscal_operation()


class l10n_br_account_fiscal_operation_line(osv.osv):
    _name = 'l10n_br_account.fiscal.operation.line'
    _description = 'Linhas das operações ficais'
    _columns = {
        'company_id': fields.many2one('res.company', 'Empresa',
                                      requeried=True),
        'fiscal_classification_id': fields.many2one(
            'account.product.fiscal.classification', 'NCM',
            domain="['|',('company_id','=',False),"
            "('company_id','=',company_id)]"),
        'tax_code_id': fields.many2one('account.tax.code',
                                       'Código do Imposto',
                                       requeried=True,
                                       domain="['|',('company_id','=',False),"
                                       "('company_id','=',company_id)]"),
        'cst_id': fields.many2one('account.tax.code',
                                  'Código de Situação Tributária',
                                  requeried=True),
        'fiscal_operation_id': fields.many2one(
            'l10n_br_account.fiscal.operation',
            'Fiscal Operation Ref', ondelete='cascade', select=True)}

l10n_br_account_fiscal_operation_line()


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
