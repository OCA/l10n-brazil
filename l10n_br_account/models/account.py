# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    revenue_expense = fields.Boolean('Gera Financeiro')


class AccountTaxComputation(models.Model):
    _name = 'account.tax.computation'

    domain = fields.Char(u'Domain', size=64)
    name = fields.Char('Name', size=64)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    domain = fields.Char('Domain', required=True, size=8)

    @api.model
    def _compute_tax(self, taxes, total_line, product, product_qty,
                     precision):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('type') == 'weight' and product:
                weight_net = product.weight_net
                float_val = product_qty * weight_net * tax['percent']
                tax['amount'] = round(float_val, precision)

            if tax.get('type') == 'quantity':
                tax['amount'] = round(product_qty * tax['percent'], precision)

            tax['amount'] = round(
                tax['amount'] * (1 - tax['base_reduction']), precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            if tax['percent']:
                tax['total_base'] = round(
                    total_line * (1 - tax['base_reduction']), precision)
                tax['total_base_other'] = round(
                    total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
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
                    - 'cr': Database cursor.
                    - 'uid': Current user.
                    - 'taxes': List with all taxes id.
                    - 'price_unit': Product price unit.
                    - 'quantity': Product quantity.
                    - 'force_excluded': Used to say that we don't want to consider
                                        the value of field price_include of tax.
                                        It's used in encoding by line where you don't
                                        matter if you encoded a tax with that boolean
                                        to True or False.
                """
        precision = self.env['decimal.precision'].precision_get('Account')
        if not currency:
	    if len(self) == 0:
	        company_id = self.env.user.company_id
            else:
	        company_id = self[0].company_id
            currency = company_id.currency_id
        taxes = self
        result = super(AccountTax, self).compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)

        totaldc = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in taxes if tx.id == tax['id']]
            if tax_list:
                tax_brw = tax_list[0]
            tax['domain'] = tax_brw.domain
            tax['type'] = tax_brw.type_tax_use
            tax['percent'] = tax_brw.amount
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.tax_discount

        common_taxes = [tx for tx in result['taxes'] if tx['domain']]
        result_tax = self._compute_tax(
            common_taxes, result['total_excluded'],
            product, quantity, precision)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        return {
            'total_excluded': result['total_excluded'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes
        }


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    def execute(self):
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
        result = super(WizardMultiChartsAccounts, self).execute()

        obj_multi = self[0]
        obj_fp_template = self.env['account.fiscal.position.template']
        obj_fp = self.env['account.fiscal.position']

        chart_template_id = obj_multi.chart_template_id.id
        company_id = obj_multi.company_id.id

        fp_template_ids = obj_fp_template.search([('chart_template_id', '=', chart_template_id)])

        for fp_template in fp_template_ids:
            if fp_template.cfop_id:
                fp_id = obj_fp.search(
                    [('name', '=', fp_template.name),
                     ('company_id', '=', company_id)])
                if fp_id:
                    fp_id.write(
                        {'cfop_id': fp_template.cfop_id.id})
        return result


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _check_allow_type_change(self, new_type, context=None):
        """Hack to allow re-shaping demo chart of account in demo mode"""
        self._cr.execute("""SELECT demo
            FROM ir_module_module WHERE name = 'l10n_br_account';""")
        if self._cr.fetchone()[0]:
            return True
        else:
            return super(AccountAccount, self)._check_allow_type_change()

    def _check_allow_code_change(self, context=None):
        """Hack to allow re-shaping demo chart of account in demo mode"""
        self._cr.execute("""SELECT demo
            FROM ir_module_module WHERE name = 'l10n_br_account';""")
        if self._cr.fetchone()[0]:
            return True
        else:
            return super(AccountAccount, self)._check_allow_code_change()
