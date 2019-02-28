# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountTax(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax'

    icms_base_type = fields.Selection(
        selection=[('0', u'Margem Valor Agregado (%)'),
                   ('1', u'Pauta (valor)'),
                   ('2', u'Preço Tabelado Máximo (valor)'),
                   ('3', u'Valor da Operação')],
        string=u'Tipo Base ICMS',
        required=True,
        default='0')

    icms_st_base_type = fields.Selection(
        selection=[('0', u'Preço tabelado ou máximo  sugerido'),
                   ('1', u'Lista Negativa (valor)'),
                   ('2', u'Lista Positiva (valor)'),
                   ('3', u'Lista Neutra (valor)'),
                   ('4', 'Margem Valor Agregado (%)'),
                   ('5', 'Pauta (valor)')],
        string=u'Tipo Base ICMS ST',
        required=True,
        default='4')

    @api.model
    def _compute_tax(self, taxes, total_line, product, product_qty,
                     precision, base_tax=0.0):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('amount_type') == 'weight' and product:
                product_read = self.env['product.product'].read(
                    product, ['weight_net'])
                tax['amount'] = round((product_qty * product_read.get(
                    'weight_net', 0.0)) * tax['percent'], precision)

            if base_tax:
                total_line = base_tax

            if tax.get('amount_type') == 'quantity':
                tax['amount'] = round(
                    product_qty * tax['percent'] / 100, precision)

            tax['amount'] = round(
                total_line * tax['percent'] / 100, precision)
            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']),
                                  precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            if tax['percent']:
                unrounded_base = total_line * (1 - tax['base_reduction'])
                tax['total_base'] = round(unrounded_base, precision)
                tax['total_base_other'] = round(
                    total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None, fiscal_position=False,
                    insurance_value=0.0, freight_value=0.0,
                    other_costs_value=0.0, base_tax=0.0):
        """ Returns all information required to apply taxes
            (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order
                as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]
        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'total_tax_discount': 0.0 # Total tax out of price
            'taxes': [{               # One dict for each tax in self
                                      # and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """
        precision = currency.decimal_places or \
            self.env['decimal.precision'].precision_get('Account')
        result = super(AccountTax, self).compute_all(
            price_unit, currency, quantity, product, partner)
        totaldc = icms_value = 0.0
        ipi_value = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in self if tx.id == tax['id']]
            if tax_list:
                tax_brw = tax_list[0]
            tax['domain'] = tax_brw.domain
            tax['amount_type'] = tax_brw.amount_type
            tax['percent'] = tax_brw.amount
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.tax_group_id.tax_discount

            if tax.get('domain') == 'icms':
                tax['icms_base_type'] = tax_brw.icms_base_type

            if tax.get('domain') == 'icmsst':
                tax['icms_st_base_type'] = tax_brw.icms_st_base_type

        common_taxes = [tx for tx in result['taxes'] if tx[
            'domain'] not in ['icms', 'icmsst', 'ipi', 'icmsinter',
                              'icmsfcp']]
        result_tax = self._compute_tax(common_taxes, result['base'],
                                       product, quantity, precision, base_tax)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        # Calcula o IPI
        specific_ipi = [tx for tx in result['taxes'] if tx['domain'] == 'ipi']
        result_ipi = self._compute_tax(specific_ipi, result['base'],
                                       product, quantity, precision, base_tax)
        totaldc += result_ipi['tax_discount']
        calculed_taxes += result_ipi['taxes']
        for ipi in result_ipi['taxes']:
            ipi_value += ipi['amount']

        # Calcula ICMS
        specific_icms = [tx for tx in result['taxes']
                         if tx['domain'] == 'icms']

        # Adiciona frete seguro e outras despesas na base do ICMS
        total_base = (result['base'] + insurance_value +
                      freight_value + other_costs_value)

        # Em caso de operação de ativo adiciona o IPI na base de ICMS
        if fiscal_position and fiscal_position.asset_operation:
            total_base += ipi_value

        result_icms = self._compute_tax(
            specific_icms,
            total_base,
            product,
            quantity,
            precision,
            base_tax)
        totaldc += result_icms['tax_discount']
        calculed_taxes += result_icms['taxes']
        if result_icms['taxes']:
            icms_value = result_icms['taxes'][0]['amount']

        # Calcula a FCP
        specific_fcp = [tx for tx in result['taxes']
                        if tx['domain'] == 'icmsfcp']
        result_fcp = self._compute_tax(specific_fcp, total_base,
                                       product, quantity, precision, base_tax)
        totaldc += result_fcp['tax_discount']
        calculed_taxes += result_fcp['taxes']

        # Calcula ICMS Interestadual (DIFAL)
        specific_icms_inter = [tx for tx in result['taxes']
                               if tx['domain'] == 'icmsinter']
        result_icms_inter = self._compute_tax(
            specific_icms_inter,
            total_base,
            product,
            quantity,
            precision,
            base_tax)

        if (specific_icms and specific_icms_inter and fiscal_position and
                partner.partner_fiscal_type_id.ind_ie_dest == '9'):

            if fiscal_position.cfop_id.id_dest == '2':

                # Calcula o DIFAL total
                result_icms_inter['taxes'][0]['amount'] = round(
                    abs(specific_icms_inter[0]['amount'] -
                        icms_value), precision
                )

                # Cria uma chave com o ICMS de intraestadual
                result_icms_inter['taxes'][0]['icms_origin_percent'] = \
                    specific_icms[0]['percent']

                # Procura o percentual de partilha vigente
                icms_partition_id = self.env[
                    'l10n_br_tax.icms_partition'].search(
                        [('date_start', '<=',
                          time.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                         ('date_end', '>=',
                          time.strftime(DEFAULT_SERVER_DATE_FORMAT))])

                # Calcula o difal de origin e destino
                if icms_partition_id:
                    result_icms_inter['taxes'][0]['icms_part_percent'] = \
                        icms_partition_id.rate / 100

                    result_icms_inter['taxes'][0]['icms_dest_value'] = \
                        round(
                            result_icms_inter['taxes'][0]['amount'] *
                            (icms_partition_id.rate / 100),
                            precision)
                    result_icms_inter['taxes'][0]['icms_origin_value'] = \
                        round(
                            result_icms_inter['taxes'][0]['amount'] *
                            ((100 - icms_partition_id.rate) / 100),
                            precision)

                # Atualiza o imposto icmsinter
                result_icms_inter['tax_discount'] = \
                    result_icms_inter['taxes'][0]['amount']
                totaldc += result_icms_inter['tax_discount']
                calculed_taxes += result_icms_inter['taxes']

        # Calcula ICMS ST
        specific_icmsst = [tx for tx in result['taxes']
                           if tx['domain'] == 'icmsst']
        result_icmsst = self._compute_tax(specific_icmsst,
                                          result['total_included'], product,
                                          quantity, precision, base_tax)
        totaldc += result_icmsst['tax_discount']
        if result_icmsst['taxes']:
            icms_st_percent = result_icmsst['taxes'][0]['percent']
            icms_st_percent_reduction = result_icmsst[
                'taxes'][0]['base_reduction']
            icms_st_base = round(((result['total_included'] + ipi_value) *
                                 (1 - icms_st_percent_reduction)) *
                                 (1 + result_icmsst['taxes'][0]['amount_mva']),
                                 precision)
            icms_st_base_other = round(
                ((result['total_included'] + ipi_value) * (
                    1 + result_icmsst['taxes'][0]['amount_mva'])),
                precision) - icms_st_base
            result_icmsst['taxes'][0]['total_base'] = icms_st_base
            result_icmsst['taxes'][0]['amount'] = round(
                (icms_st_base * icms_st_percent) - icms_value, precision)
            result_icmsst['taxes'][0]['icms_st_percent'] = icms_st_percent
            result_icmsst['taxes'][0][
                'icms_st_percent_reduction'] = icms_st_percent_reduction
            result_icmsst['taxes'][0][
                'icms_st_base_other'] = icms_st_base_other

            if result_icmsst['taxes'][0]['percent']:
                calculed_taxes += result_icmsst['taxes']

        # Estimate Taxes
        if fiscal_position and fiscal_position.asset_operation:
            if product.origin in ('1', '2', '6', '7'):
                total_taxes = ((result['total_included'] - totaldc) *
                               (product.estd_import_taxes_perct or 0.0)/100)
            else:
                total_taxes = ((result['total_included'] - totaldc) *
                               (product.estd_national_taxes_perct or 0.0)/100)
            result['total_taxes'] = round(total_taxes, precision)

        result.update({
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes,
        })

        return result
