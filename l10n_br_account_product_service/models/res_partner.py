# -*- coding: utf-8 -*-
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

from openerp import models, fields, api


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.v7
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = []
        if not context:
            context = {}
        if fposition_id and fposition_id.company_id and \
        context.get('type_tax_use') in ('sale', 'all'):
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
                    ok = True
            if not ok:
                result.append(t.id)

        return list(set(result))

    @api.multi
    def _map_tax(self, product_id, taxes):
        result = {}
        product = self.env['product.product'].browse(product_id)
        if self.company_id and self.env.context.get('type_tax_use') in ('sale', 'all'):
            if self.env.context.get('fiscal_type', 'product') == 'product':
                company_taxes = self.company_id.product_tax_definition_line
                for tax_def in company_taxes:
                    if tax_def.tax_id:
                        taxes |= tax_def.tax_id
                        result[tax_def.tax_id.domain] = {
                            'tax': tax_def.tax_id,
                            'tax_code': tax_def.tax_code_id,
                        }
            else:
                company_taxes = self.company_id.service_tax_definition_line
                for tax_def in company_taxes:
                    if tax_def.tax_id:
                        taxes |= tax_def.tax_id
                        result[tax_def.tax_id.domain] = {
                            'tax': tax_def.tax_id,
                            'tax_code': tax_def.tax_code_id,
                        }
            product_ncm_tax_def = product.ncm_id.sale_tax_definition_line

        else:
            product_ncm_tax_def = product.ncm_id.purchase_tax_definition_line

        for ncm_tax_def in product_ncm_tax_def:
            if ncm_tax_def.tax_id:
                result[ncm_tax_def.tax_id.domain] = {
                    'tax': ncm_tax_def.tax_id,
                    'tax_code': ncm_tax_def.tax_code_id,
                }

        map_taxes = self.env['account.fiscal.position.tax'].browse()
        map_taxes_ncm = self.env['account.fiscal.position.tax'].browse()
        for tax in taxes:
            for map in self.tax_ids:
                if map.tax_src_id == tax or map.tax_code_src_id == tax.tax_code_id:
                    if map.tax_dest_id or tax.tax_code_id:
                        if map.ncm_id == product.ncm_id:
                            map_taxes_ncm |= map
                        else:
                            map_taxes |= map
            else:
                if result.get(tax.domain):
                    result[tax.domain].update({'tax': tax})
                else:
                    result[tax.domain] = {'tax': tax}

        result.update(self._map_tax_code(map_taxes))
        result.update(self._map_tax_code(map_taxes_ncm))
        return result

    @api.v8
    def map_tax(self, taxes):
        result = self.env['account.tax'].browse()
        taxes_codes = self._map_tax(self.env.context.get('product_id'), taxes)
        for tax in taxes_codes:
            if taxes_codes[tax].get('tax'):
                result |= taxes_codes[tax].get('tax')
        return result


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    # TODO migrate to new API
    @api.v7
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
