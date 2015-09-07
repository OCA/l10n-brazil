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

from openerp import api, models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    revenue_expense = fields.Boolean(string='Gera Financeiro',
         help=u"Marque esta caixa para diários de faturas que gerem contas a pagar e a receber")


class AccountTaxComputation(models.Model):
    _name = 'account.tax.computation'

    name = fields.Char(string='Name', size=64)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _compute_tax(self,cr, uid, taxes, total_line, product, product_qty,
                     precision):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('type') == 'weight' and product:
                product_read = self.pool.get('product.product').read(
                    cr, uid, product, ['weight_net'])
                tax['amount'] = round((product_qty * product_read.get('weight_net', 0.0)) * tax['percent'], precision)

            if tax.get('type') == 'quantity':
                tax['amount'] = round(product_qty * tax['percent'], precision)

            tax['amount'] = round(total_line * tax['percent'], precision)
            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']), precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            if tax['percent']:
                tax['total_base'] = round(total_line * (1 - tax['base_reduction']), precision)
                tax['total_base_other'] = round(total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    @api.v7
    def compute_all(self,cr, uid, taxes, price_unit, quantity,
                    product=None, partner=None, force_excluded=False,
                    fiscal_position=False, insurance_value=0.0,
                    freight_value=0.0, other_costs_value=0.0):
        """Compute taxes

        Returns a dict of the form::

        {
            'total': Total without taxes,
            'total_included': Total with taxes,
            'total_tax_discount': Total Tax Discounts,
            'taxes': <list of taxes, objects>,
            'total_base': Total Base by tax,
        }

        :Parameters:            
            - 'taxes': List with all taxes id.
            - 'price_unit': Product price unit.
            - 'quantity': Product quantity.
            - 'force_excluded': Used to say that we don't want to consider
                                the value of field price_include of tax.
                                It's used in encoding by line where you don't
                                matter if you encoded a tax with that boolean
                                to True or False.
        """
        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(cr, uid, 'Account')
        result = super(AccountTax, self).compute_all(cr, uid, taxes,
            price_unit, quantity, product, partner, force_excluded)
        totaldc = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in taxes if tx.id == tax['id']]
            if tax_list:
                tax_brw = tax_list[0]
            tax['domain'] = tax_brw.domain
            tax['type'] = tax_brw.type
            tax['percent'] = tax_brw.amount
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.base_code_id.tax_discount

        common_taxes = [tx for tx in result['taxes'] if tx['domain']]
        result_tax = self._compute_tax(cr, uid, common_taxes, result['total'],
            product, quantity, precision)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        return {
            'total': result['total'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes
        }

    @api.v8
    def compute_all(self, price_unit, quantity,
                    product=None, partner=None, force_excluded=False,
                    fiscal_position=False, insurance_value=0.0,
                    freight_value=0.0, other_costs_value=0.0):
        return self._model.compute_all(
            self._cr, self._uid, self, price_unit, quantity,
            product=product, partner=partner, force_excluded=force_excluded,
            fiscal_position=fiscal_position, insurance_value=insurance_value,
            freight_value=freight_value, other_costs_value=other_costs_value)


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    def execute(self, cr, uid, ids, context=None):
        """This function is called at the confirmation of the wizard to
        generate the COA from the templates. It will read all the provided
        information to create the accounts, the banks, the journals, the
        taxes, the tax codes, the accounting properties... accordingly for
        the chosen company.

        This is override in Brazilian Localization to copy CFOP
        from fiscal positions template to fiscal positions.

        :Parameters:
            - 'cr': Database cursor.
            - 'uid': Current user.
            - 'ids': orm_memory id used to read all data.
            - 'context': Context.
        """
        result = super(WizardMultiChartsAccounts, self).execute(
            cr, uid, ids, context)

        obj_multi = self.browse(cr, uid, ids[0])
        obj_fp_template = self.pool.get('account.fiscal.position.template')
        obj_fp = self.pool.get('account.fiscal.position')

        chart_template_id = obj_multi.chart_template_id.id
        company_id = obj_multi.company_id.id

        fp_template_ids = obj_fp_template.search(cr, uid,
            [('chart_template_id', '=', chart_template_id)])

        for fp_template in obj_fp_template.browse(cr, uid, fp_template_ids,
                                                  context=context):
            if fp_template.cfop_id:
                fp_id = obj_fp.search(cr, uid,
                    [('name', '=', fp_template.name),
                     ('company_id', '=', company_id)])

                if fp_id:
                    obj_fp.write(cr, uid, fp_id,
                        {'cfop_id': fp_template.cfop_id.id})
        return result


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _check_allow_type_change(self, cr, uid, ids, new_type, context=None):
        """Hack to allow re-shaping demo chart of account in demo mode"""
        cr.execute("""SELECT demo
            FROM ir_module_module WHERE name = 'l10n_br_account';""")
        if cr.fetchone()[0]:
            return True
        else:
            return super(AccountAccount, self)._check_allow_type_change(
                cr, uid, ids, context)

    def _check_allow_code_change(self, cr, uid, ids, context=None):
        """Hack to allow re-shaping demo chart of account in demo mode"""
        cr.execute("""SELECT demo
            FROM ir_module_module WHERE name = 'l10n_br_account';""")
        if cr.fetchone()[0]:
            return True
        else:
            return super(AccountAccount, self)._check_allow_code_change(
                cr, uid, ids, context)
