# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
         ('2', 'Outros')], 'Indicador de Pagamento', default='1')


class AccountTaxTemplate(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax.template'

    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
         ('2', 'Preço Tabelado Máximo (valor)'),
         ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
    icms_st_base_type = fields.Selection(
        [('0', 'Preço tabelado ou máximo  sugerido'),
         ('1', 'Lista Negativa (valor)'),
         ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
         ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')


class AccountTax(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax'

    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
         ('2', 'Preço Tabelado Máximo (valor)'),
         ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
    icms_st_base_type = fields.Selection(
        [('0', 'Preço tabelado ou máximo  sugerido'),
         ('1', 'Lista Negativa (valor)'),
         ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
         ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')

    def _compute_tax(self, cr, uid, taxes, total_line, product, product_qty,
                     precision, base_tax=0.0):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('type') == 'weight' and product:
                product_read = self.pool.get('product.product').read(
                    cr, uid, product, ['weight_net'])
                tax['amount'] = round((product_qty * product_read.get(
                    'weight_net', 0.0)) * tax['percent'], precision)

            if base_tax:
                total_line = base_tax

            if tax.get('type') == 'quantity':
                tax['amount'] = round(product_qty * tax['percent'], precision)

            tax['amount'] = round(total_line * tax['percent'], precision)
            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']),
                                  precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            if tax['percent']:
                unrounded_base = total_line * (1 - tax['base_reduction'])
                tax['total_base'] = round(unrounded_base, precision)
                tax['total_base_other'] = round(total_line - tax['total_base'],
                                                precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    # TODO
    # Refatorar este método, para ficar mais simples e não repetir
    # o que esta sendo feito no método l10n_br_account_product
    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity,
                    product=None, partner=None, force_excluded=False,
                    fiscal_position=False, insurance_value=0.0,
                    freight_value=0.0, other_costs_value=0.0, base_tax=0.0):
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
                                                     price_unit, quantity,
                                                     product, partner,
                                                     force_excluded)
        totaldc = icms_value = 0.0
        ipi_value = 0.0
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

            if tax.get('domain') == 'icms':
                tax['icms_base_type'] = tax_brw.icms_base_type

            if tax.get('domain') == 'icmsst':
                tax['icms_st_base_type'] = tax_brw.icms_st_base_type

        common_taxes = [tx for tx in result['taxes'] if tx[
            'domain'] not in ['icms', 'icmsst', 'ipi', 'icmsinter']]
        result_tax = self._compute_tax(cr, uid, common_taxes, result['total'],
                                       product, quantity, precision, base_tax)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        # Calcula o IPI
        specific_ipi = [tx for tx in result['taxes'] if tx['domain'] == 'ipi']
        result_ipi = self._compute_tax(cr, uid, specific_ipi, result['total'],
                                       product, quantity, precision, base_tax)
        # Calcula a FCP
        specific_fcp = [tx for tx in result['taxes']
                        if tx['domain'] == 'icmsfcp']
        result_fcp = self._compute_tax(cr, uid, specific_fcp, result['total'],
                                       product, quantity, precision, base_tax)
        totaldc += result_ipi['tax_discount']
        calculed_taxes += result_ipi['taxes']
        for ipi in result_ipi['taxes']:
            ipi_value += ipi['amount']

        # Calcula ICMS
        specific_icms = [tx for tx in result['taxes']
                         if tx['domain'] == 'icms']
        difa = {}
        if fiscal_position and fiscal_position.asset_operation:
            total_base = result['total'] + insurance_value + \
                freight_value + other_costs_value + ipi_value

            # Para operações fora do estado e aquisição de ativo
            # TODO: Verificar se existem outras condições que
            # devem passar por este trecho
            if fiscal_position and fiscal_position.cfop_id.id_dest == '2':
                specific_icms_inter = [tx for tx in result['taxes']
                                 if tx['domain'] == 'icmsinter']
                try:
                # Devido as operações com redução de base devemos verificar os
                # totais da operação
                    if (specific_icms_inter[0]['amount'] == \
                            specific_icms[0]['amount']):
                        pass
                    elif (specific_icms_inter[0]['amount'] <
                              specific_icms[0]['amount']):
                        aux = specific_icms_inter[0]
                        specific_icms_inter[0] = specific_icms[0]['amount']
                        specific_icms[0]['amount'] = aux
                    else:
                        # BASE UNICA
                        difa['vBCUFDest'] = total_base
                        #ICMS origem = [BC x ALQ INTER]
                        difa['pICMSUFDest'] = specific_icms_inter[0]['percent']
                        #TODO mapear percentual com l10n_br_tax.icms_partition
                        difa['pICMSInterPart'] = 0.40
                        #ICMS interno Destino = [BC x ALQ intra]
                        difa['pICMSInter'] = specific_icms[0]['percent']
                        #ICMS destino = [BC x ALQ intra] - ICMS origem
                        icms_difa = ((difa['vBCUFDest'] * difa['pICMSUFDest'])-
                                     (difa['vBCUFDest'] * difa['pICMSInter']))
                        if result_fcp['taxes']:
                            # % Fundo pobreza
                            difa['pFCPUFDest'] = \
                                result_fcp['taxes'][0]['percent']
                            difa['vFCPUFDest'] = \
                                difa['vBCUFDest'] * difa['pFCPUFDest']
                            # FIXME: O ICMS deve ter o FCP incluso?
                            icms_difa -= difa['vFCPUFDest']
                        difa['vICMSUFDest'] = \
                            icms_difa * difa['pICMSInterPart']
                        difa['vICMSUFRemet'] = \
                            icms_difa * (1-difa['pICMSInterPart'])
                        specific_icms_inter[0]['percent'] = \
                            difa['pICMSUFDest'] - difa['pICMSInter']
                        #FIXME: Criar um lancaçamento para cada % rateado
                        specific_icms_inter[0]['amount'] = icms_difa
                        result_icms_inter = self._compute_tax(
                            cr,
                            uid,
                            specific_icms_inter,
                            total_base,
                            product,
                            quantity,
                            precision,
                            base_tax)
                        totaldc += result_icms_inter['tax_discount']
                        calculed_taxes += result_icms_inter['taxes']

                except:
                    raise UserError(u'Tributação do ICMS para a UF de destino',
                              u'Configurada incorretamente')

        else:
            total_base = result['total'] + insurance_value + \
                freight_value + other_costs_value

        result_icms = self._compute_tax(
            cr,
            uid,
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

        # Calcula ICMS ST
        specific_icmsst = [tx for tx in result['taxes']
                           if tx['domain'] == 'icmsst']
        result_icmsst = self._compute_tax(cr, uid, specific_icmsst,
                                          result['total'], product,
                                          quantity, precision, base_tax)
        totaldc += result_icmsst['tax_discount']
        if result_icmsst['taxes']:
            icms_st_percent = result_icmsst['taxes'][0]['percent']
            icms_st_percent_reduction = result_icmsst[
                'taxes'][0]['base_reduction']
            icms_st_base = round(((result['total'] + ipi_value) *
                                 (1 - icms_st_percent_reduction)) *
                                 (1 + result_icmsst['taxes'][0]['amount_mva']),
                                 precision)
            icms_st_base_other = round(
                ((result['total'] + ipi_value) * (
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
            total_taxes = ((result['total_included'] - totaldc) *
                           product.product_estimated_taxes_percent/100)
            result['total_taxes'] = round(total_taxes, precision)

        return {
            'total': result['total'],
            'total_included': result.get('total_included', 0.00),
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes,
            'total_taxes': result.get('total_taxes', 0.00),
        }

    @api.v8
    def compute_all(self, price_unit, quantity, product=None, partner=None,
                    force_excluded=False, fiscal_position=False,
                    insurance_value=0.0, freight_value=0.0,
                    other_costs_value=0.0, base_tax=0.00):
        return self._model.compute_all(
            self._cr, self._uid, self, price_unit, quantity,
            product=product, partner=partner,
            force_excluded=force_excluded,
            fiscal_position=fiscal_position, insurance_value=insurance_value,
            freight_value=freight_value, other_costs_value=other_costs_value,
            base_tax=base_tax)
