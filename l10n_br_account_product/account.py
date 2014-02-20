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


class AccountPaymentTerm(orm.Model):
    _inherit = 'account.payment.term'
    _columns = {
        'indPag': fields.selection(
            [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
            ('2', 'Outros')], 'Indicador de Pagamento'),
    }
    _defaults = {
        'indPag': '1',
    }


class AccountTax(orm.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax'

    def _compute_tax(self, cr, uid, taxes, total_line, product, product_qty,
                     precision):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('type') == 'weight' and product:
                product_read = self.pool.get('product.product').read(
                    cr, uid, product, ['weight_net'])
                tax['amount'] = round((product_qty * product_read.get(
                    'weight_net', 0.0)) * tax['percent'], precision)

            if tax.get('type') == 'quantity':
                tax['amount'] = round(product_qty * tax['percent'], precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            tax['amount'] = round(total_line * tax['percent'], precision)
            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']), precision)
            if tax['percent']:
                tax['total_base'] = round(total_line * (1 - tax['base_reduction']), precision)
                tax['total_base_other'] = round(total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    #TODO
    #Refatorar este método, para ficar mais simples e não repetir
    #o que esta sendo feito no método l10n_br_account_product
    def compute_all(self, cr, uid, taxes, price_unit, quantity,
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
        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(cr, uid, 'Account')
        result = super(AccountTax, self).compute_all(cr, uid, taxes,
            price_unit, quantity, product, partner, force_excluded)
        totaldc = icms_base = icms_value = icms_percent = ipi_value = 0.0
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

        common_taxes = [tx for tx in result['taxes'] if tx['domain'] not in ['icms', 'icmsst', 'ipi']]
        result_tax = self._compute_tax(cr, uid, common_taxes, result['total'],
            product, quantity, precision)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        # Calcula o IPI
        specific_ipi = [tx for tx in result['taxes'] if tx['domain'] == 'ipi']
        result_ipi = self._compute_tax(cr, uid, specific_ipi, result['total'],
            product, quantity, precision)
        totaldc += result_ipi['tax_discount']
        calculed_taxes += result_ipi['taxes']
        for ipi in result_ipi['taxes']:
            ipi_value += ipi['amount']

        # Calcula ICMS
        specific_icms = [tx for tx in result['taxes'] if tx['domain'] == 'icms']
        if fiscal_position and fiscal_position.asset_operation:
            total_base = result['total'] + insurance_value + \
            freight_value + other_costs_value + ipi_value
        else:
            total_base = result['total'] + insurance_value + \
            freight_value + other_costs_value

        result_icms = self._compute_tax(
            cr, uid, specific_icms, total_base, product, quantity, precision)
        totaldc += result_icms['tax_discount']
        calculed_taxes += result_icms['taxes']
        if result_icms['taxes']:
            icms_base = result_icms['taxes'][0]['total_base']
            icms_value = result_icms['taxes'][0]['amount']
            icms_percent = result_icms['taxes'][0]['percent']
            icms_percent_reduction = result_icms['taxes'][0]['base_reduction']

        # Calcula ICMS ST
        specific_icmsst = [tx for tx in result['taxes'] if tx['domain'] == 'icmsst']
        result_icmsst = self._compute_tax(cr, uid, specific_icmsst, result['total'], product, quantity, precision)
        totaldc += result_icmsst['tax_discount']
        if result_icmsst['taxes']:
            icms_st_percent = result_icmsst['taxes'][0]['percent'] or icms_percent
            icms_st_percent_reduction = result_icmsst['taxes'][0]['base_reduction'] or icms_percent_reduction
            icms_st_base = round(((icms_base + ipi_value) * (1 + result_icmsst['taxes'][0]['amount_mva'])), precision)
            icms_st_base_other = round(((result['total'] + ipi_value) * (1 + result_icmsst['taxes'][0]['amount_mva'])), precision) - icms_st_base
            result_icmsst['taxes'][0]['total_base'] = icms_st_base
            result_icmsst['taxes'][0]['amount'] = round((icms_st_base  * icms_st_percent) - icms_value, precision)
            result_icmsst['taxes'][0]['icms_st_percent'] = icms_st_percent
            result_icmsst['taxes'][0]['icms_st_percent_reduction'] = icms_st_percent_reduction
            result_icmsst['taxes'][0]['icms_st_base_other'] = icms_st_base_other

            if result_icmsst['taxes'][0]['amount_mva']:
                calculed_taxes += result_icmsst['taxes']

        print "CALCULO ICMS ST", result_icmsst['taxes']

        return {
            'total': result['total'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes
        }