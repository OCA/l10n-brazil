# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
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

FISCAL_POSITION_COLUMNS = {
    'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
    'fiscal_category_id': fields.many2one('l10n_br_account.fiscal.category',
                                          'Categoria Fiscal'),
    'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')],
                             'Tipo'),
    'type_tax_use': fields.selection([('sale','Sale'),
                                      ('purchase','Purchase'),
                                      ('all','All')], 'Tax Application'),
    'fiscal_category_fiscal_type': fields.related(
        'fiscal_category_id', 'fiscal_type', type='char', readonly=True,
        relation='l10n_br_account.fiscal.category', store=True,
        string='Fiscal Type'),
    'inv_copy_note': fields.boolean('Copiar Observação na Nota Fiscal'),
    'asset_operation': fields.boolean('Operação de Aquisição de Ativo',
                                      help="Caso seja marcada essa opção, \
                                        será incluido o IPI na base de \
                                        calculo do ICMS.")}


class account_fiscal_position_template(osv.osv):
    _inherit = 'account.fiscal.position.template'
    _columns = FISCAL_POSITION_COLUMNS
    
    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purhcase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'), 
                          'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        if fiscal_category_id:
             fc_fields = self.pool.get(
                'l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id, ['fiscal_type',
                                                  'journal_type'], context=context)
        return {'value': 
            {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}
        
    def generate_fiscal_position(self, cr, uid, chart_temp_id, tax_template_ref, acc_template_ref, company_id, context=None):
        """
        This method generate Fiscal Position, Fiscal Position Accounts and Fiscal Position Taxes from templates.

        :param chart_temp_id: Chart Template Id.
        :param taxes_ids: Taxes templates reference for generating account.fiscal.position.tax.
        :param acc_template_ref: Account templates reference for generating account.fiscal.position.account.
        :param company_id: company_id selected from wizard.multi.charts.accounts.
        :returns: True
        """
        if context is None:
            context = {}

        obj_tax_fp = self.pool.get('account.fiscal.position.tax')
        obj_ac_fp = self.pool.get('account.fiscal.position.account')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_tax_code = self.pool.get('account.tax.code')
        obj_tax_code_template = self.pool.get('account.tax.code.template')
        tax_code_template_ref = {}
        tax_code_ids = obj_tax_code.search(
            cr, uid, [('company_id', '=', company_id)])
                
        for tax_code in obj_tax_code.browse(cr, uid, tax_code_ids):
            tax_code_template = obj_tax_code_template.search(cr,uid,[('name', '=', tax_code.name)])
            if tax_code_template:
                tax_code_template_ref[tax_code_template[0]] = tax_code.id
        
        fp_ids = self.search(cr, uid, [('chart_template_id', '=', chart_temp_id)])
        for position in self.browse(cr, uid, fp_ids, context=context):
            new_fp = obj_fiscal_position.create(
                cr, uid, {'company_id': company_id,
                          'name': position.name,
                          'note': position.note,
                          'type': position.type,
                          'type_tax_use': position.type_tax_use,
                          'cfop_id': position.cfop_id and position.cfop_id.id or False,
                          'inv_copy_note': position.inv_copy_note,
                          'asset_operation': position.asset_operation,
                          'fiscal_category_id': position.fiscal_category_id and position.fiscal_category_id.id or False})
            for tax in position.tax_ids:
                obj_tax_fp.create(cr, uid, {
                    'tax_src_id': tax.tax_src_id and tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id': tax.tax_code_src_id and tax_code_template_ref.get(tax.tax_code_src_id.id, False),
                    'tax_src_domain': tax.tax_src_domain,
                    'tax_dest_id': tax.tax_dest_id and tax_template_ref.get(tax.tax_dest_id.id, False),
                    'tax_code_dest_id': tax.tax_code_dest_id and tax_code_template_ref.get(tax.tax_code_dest_id.id, False),
                    'position_id': new_fp
                })
            for acc in position.account_ids:
                obj_ac_fp.create(cr, uid, {
                    'account_src_id': acc_template_ref[acc.account_src_id.id],
                    'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                    'position_id': new_fp
                })
        return True

account_fiscal_position_template()


class account_fiscal_position_tax_template(osv.osv):
    _inherit = 'account.fiscal.position.tax.template'
    _columns = {
        'tax_src_id': fields.many2one('account.tax.template', 'Tax Source'),
        'tax_code_src_id': fields.many2one('account.tax.code.template',
                                            u'Código Taxa Origem'),
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code.template',
                                            'Replacement Tax Code')}

    def onchange_tax_src_id(self, cr, uid, ids,
                            tax_src_id=False, context=None):
        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax.template').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']
        return {'value': {'tax_src_domain': tax_domain}}

account_fiscal_position_tax_template()


class account_fiscal_position(osv.osv):
    _inherit = 'account.fiscal.position'
    _columns = FISCAL_POSITION_COLUMNS
    
    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purchase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'),
                          'tax_ids': False}}
    
    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        fiscal_category_fields = False
        if fiscal_category_id:
             fc_fields = self.pool.get(
                'l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id, ['fiscal_type',
                                                  'journal_type'], context=context)
        return {'value':
            {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}
        
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = []
        if not context:
            context = {}
        if fposition_id and fposition_id.company_id and \
        context.get('type_tax_use', 'all') in ('sale', 'all'):
            if context.get('fiscal_type', 'product') == 'product':
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['product_tax_ids'],
                    context=context)['product_tax_ids']
            else:
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['service_tax_ids'],
                    context=context)['service_tax_ids']

            company_taxes = self.pool.get('account.tax').browse(
                    cr, uid, company_tax_ids, context=context)
            if taxes:
                all_taxes = taxes + company_taxes
            else:
                all_taxes = company_taxes
            taxes = all_taxes

        if not taxes:
            return []
        if not fposition_id:
            return map(lambda x: x.id, taxes)
        for t in taxes:
            ok = False
            tax_src = False
            for tax in fposition_id.tax_ids:
                tax_src = tax.tax_src_id and tax.tax_src_id.id == t.id
                tax_code_src = tax.tax_code_src_id and \
                    tax.tax_code_src_id.id == t.tax_code_id.id
                    
                if tax_src or tax_code_src:
                    if tax.tax_dest_id:
                        result.append(tax.tax_dest_id.id)
                    ok=True
            if not ok:
                result.append(t.id)

        return list(set(result))

account_fiscal_position()


class account_fiscal_position_tax(osv.osv):
    _inherit = 'account.fiscal.position.tax'
    _columns = {
        'tax_src_id': fields.many2one('account.tax', 'Tax Source'),
        'tax_code_src_id': fields.many2one('account.tax.code',
                                            u'Código Taxa Origem'),
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code',
                                            'Replacement Tax Code')}

    def onchange_tax_src_id(self, cr, uid, ids,
                            tax_src_id=False, context=None):
        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']
        return {'value': {'tax_src_domain': tax_domain}}

account_fiscal_position_tax()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'partner_fiscal_type_id': fields.many2one(
            'l10n_br_account.partner.fiscal.type',
            'Tipo Fiscal do Parceiro',
            domain="[('tipo_pessoa','=',tipo_pessoa)]")}

res_partner()
