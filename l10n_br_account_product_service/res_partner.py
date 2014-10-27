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

FISCAL_POSITION_COLUMNS = {
    'fiscal_category_id': fields.many2one('l10n_br_account.fiscal.category',
        'Categoria Fiscal'),
    'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')],
        'Tipo'),
    'type_tax_use': fields.selection([('sale', 'Sale'),
                                      ('purchase', 'Purchase'),
                                      ('all', 'All')], 'Tax Application'),
    'inv_copy_note': fields.boolean('Copiar Observação na Nota Fiscal')}


class AccountFiscalPositionTemplate(orm.Model):
    _inherit = 'account.fiscal.position.template'
    _columns = FISCAL_POSITION_COLUMNS

    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purhcase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'),
                          'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        if fiscal_category_id:
            fc_fields = self.pool.get('l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id,
                    ['fiscal_type', 'journal_type'], context=context)
        return {'value':
            {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}

    def generate_fiscal_position(self, cr, uid, chart_temp_id,
                                 tax_template_ref, acc_template_ref,
                                 company_id, context=None):
        """
        This method generate Fiscal Position, Fiscal Position Accounts and
        Fiscal Position Taxes from templates.

        :param chart_temp_id: Chart Template Id.
        :param taxes_ids: Taxes templates reference for generating
        account.fiscal.position.tax.
        :param acc_template_ref: Account templates reference for generating
        account.fiscal.position.account.
        :param company_id: selected from wizard.multi.charts.accounts.
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
            tax_code_template = obj_tax_code_template.search(
                cr, uid, [('name', '=', tax_code.name)])
            if tax_code_template:
                tax_code_template_ref[tax_code_template[0]] = tax_code.id

        fp_ids = self.search(cr, uid,
            [('chart_template_id', '=', chart_temp_id)])
        for position in self.browse(cr, uid, fp_ids, context=context):
            new_fp = obj_fiscal_position.create(
                cr, uid, {'company_id': company_id,
                          'name': position.name,
                          'note': position.note,
                          'type': position.type,
                          'type_tax_use': position.type_tax_use,
                          'inv_copy_note': position.inv_copy_note,
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


class AccountFiscalPositionTaxTemplate(orm.Model):
    _inherit = 'account.fiscal.position.tax.template'
    _columns = {
        'tax_src_id': fields.many2one('account.tax.template', 'Tax Source'),
        'tax_code_src_id': fields.many2one('account.tax.code.template',
                                            u'Código Taxa Origem'),
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code.template',
                                            'Replacement Tax Code')
    }

    def _tax_domain(self, cr, uid, ids, tax_src_id=False,
                    tax_code_src_id=False, context=None):

        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax.template').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']

        if tax_code_src_id:
            tax_domain = self.pool.get('account.tax.code.template').read(
                cr, uid, tax_code_src_id, ['domain'],
                context=context)['domain']

        return {'value': {'tax_src_domain': tax_domain}}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False,
                            tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)

    def onchange_tax_code_src_id(self, cr, uid, ids, tax_src_id=False,
                                 tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)


class AccountFiscalPosition(orm.Model):
    _inherit = 'account.fiscal.position'
    _columns = FISCAL_POSITION_COLUMNS

    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purchase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'),
                          'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        if fiscal_category_id:
            fc_fields = self.pool.get('l10n_br_account.fiscal.category').read(
                cr, uid, fiscal_category_id, ['fiscal_type', 'journal_type'],
                context=context)
        return {'value':
            {'fiscal_category_fiscal_type': fc_fields['fiscal_type']}}


class AccountFiscalPositionTax(orm.Model):
    _inherit = 'account.fiscal.position.tax'
    _columns = {
        'tax_src_id': fields.many2one('account.tax', 'Tax Source'),
        'tax_code_src_id': fields.many2one('account.tax.code',
                                            u'Código Taxa Origem'),
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code',
                                            'Replacement Tax Code')
    }

    def _tax_domain(self, cr, uid, ids, tax_src_id=False,
                    tax_code_src_id=False, context=None):

        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']

        if tax_code_src_id:
            tax_domain = self.pool.get('account.tax.code').read(
                cr, uid, tax_code_src_id, ['domain'],
                context=context)['domain']

        return {'value': {'tax_src_domain': tax_domain}}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False,
                            tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)

    def onchange_tax_code_src_id(self, cr, uid, ids, tax_src_id=False,
                                 tax_code_src_id=False, context=None):

        return self._tax_domain(cr, uid, ids, tax_src_id, tax_code_src_id,
                                context=context)