# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Luiz Felipe do Divino
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import fields, models, api
from ..bradesco import bradesco_tax
from datetime import datetime
from openerp.addons import decimal_precision as dp


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)
        if payment_order.mode.type.code == 'gnre':
            if payment_order.mode.payment_order_type == 'tributos':
                domain += [
                    ('debit', '>', 0)
                ]
            # for i in domain:
            #     del i
            tax_code_ids = self.env[
                'account.tax.code'].search([('domain', '=', 'icms')])

            domain.append(('tax_code_id', 'in', tax_code_ids.ids))
        return True

    @api.multi
    def _prepare_payment_line(self, payment, line):
        res = super(PaymentOrderCreate, self)._prepare_payment_line(
            payment, line
        )
        res['amount_currency'] = line.tax_amount
        res['date'] = line.date
        res.update({'ml_maturity_date': line.date})
        return res

    @api.multi
    def create_payment(self):
        super(PaymentOrderCreate, self).create_payment()

        parser_gnre = bradesco_tax.BradescoGnre()

        arq = open('/tmp/testeGNRE', 'w')

        texto = ''

        for line in self.entries:
            if line.partner_id.is_company:
                tipo_inscricao = '2'
            else:
                tipo_inscricao = '1'

            if str(line.credit)[-2] == '.':
                valor_tributo = str(line.credit).replace('.', '') + '0'

            endereco01 = str(line.partner_id.street)
            # endereco02 = str(line.partner_id.street2.replace('º', ''))
            endereco_cliente = endereco01
            vals = {
                'identificador_tributo': 'G',
                'nome_cliente': str(line.partner_id.name),
                'endereco_cliente': endereco_cliente,
                'cep_cliente': str(line.partner_id.zip.replace('-', '')),
                'uf_cliente': str(line.partner_id.state_id.code),
                'autoriza_pagamento': 'S',
                'tipo_inscricao': tipo_inscricao,
                'uf_favorecida': str(line.partner_id.state_id.code),
                'telefone_cliente': str(line.partner_id.phone
                                        .replace('(', '').replace(')', '')
                                        .replace('-', '').replace(' ', '')),
                'numero_inscricao': str(line.partner_id.cnpj_cpf
                                        .replace('.', '').replace('/', '')
                                        .replace('-', '')),
                'valor_do_principal': valor_tributo,
                'data_pagamento_tributo': line.date.replace('-', ''),
                'data_vencimento_tributo': line.date.replace('-', ''),
                'num_doc_origem': str(line.invoice.display_name),
            }

            linha_arquivo = parser_gnre.remessa(**vals)
            texto += linha_arquivo
            texto += '\n'
            print linha_arquivo

        arq.write(texto)
        arq.close()

        return True


class GnrePartner(models.Model):
    _inherit = "res.partner"

    gerar_gnre = fields.Boolean("Gera GNRE")
    prazo_gnre = fields.Integer("Prazo de GNRE")


class GuiaRecolhimento(models.Model):
    _name = "guia.recolhimento"

    codigo = fields.Char("Codigo de recolhimento")
    descricao = fields.Text(u"Descrição")


class AccountInvoiceSeparetedTaxes(models.Model):
    _inherit = 'account.invoice'

    icms_st_value_total = fields.Float(
        'Total de Subsituição Tributária antecipada em nome do cliente',
        digits=dp.get_precision('Account'), default=0.00)
    gerar_gnre = fields.Boolean("Gerar GNRE", related='partner_id.gerar_gnre',
                                store=True)

    @api.multi
    @api.depends('invoice_line', 'tax_line.amount')
    def _compute_amount(self):
        super(AccountInvoiceSeparetedTaxes, self)._compute_amount()

        self.amount_total = self.amount_untaxed + \
            self.amount_costs + self.amount_insurance + self.amount_freight

        self.write({'icms_st_value_total': self.icms_st_value})

class AccountInvoiceProductIcmsst(models.Model):
    _inherit = 'account.invoice.line'

class AccountInvoiceTaxes(models.Model):
    _inherit = 'account.tax'

    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity,
                    product=None, partner=None, force_excluded=False,
                    fiscal_position=False, insurance_value=0.0,
                    freight_value=0.0, other_costs_value=0.0, base_tax=0.0):

        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(cr, uid, 'Account')
        result = super(AccountInvoiceTaxes, self).compute_all(cr, uid, taxes,
                                                              price_unit,
                                                              quantity, product,
                                                              partner,
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
            'domain'] not in ['icms', 'icmsst', 'ipi']]
        result_tax = self._compute_tax(cr, uid, common_taxes, result['total'],
                                       product, quantity, precision, base_tax)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        # Calcula o IPI
        specific_ipi = [tx for tx in result['taxes'] if tx['domain'] == 'ipi']
        result_ipi = self._compute_tax(cr, uid, specific_ipi, result['total'],
                                       product, quantity, precision, base_tax)
        totaldc += result_ipi['tax_discount']
        calculed_taxes += result_ipi['taxes']
        for ipi in result_ipi['taxes']:
            ipi_value += ipi['amount']

        # Calcula ICMS
        specific_icms = [tx for tx in result['taxes']
                         if tx['domain'] == 'icms']
        if fiscal_position and fiscal_position.asset_operation:
            total_base = result['total'] + insurance_value + \
                freight_value + other_costs_value + ipi_value
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

            if result_icmsst['taxes'][0]['percent'] and not partner.gerar_gnre:
                calculed_taxes += result_icmsst['taxes']
            elif result_icmsst['taxes'][0]['percent']:
                result['total_st'] = result_icmsst['taxes']

        # Estimate Taxes
        if fiscal_position and fiscal_position.asset_operation:
            obj_tax_estimate = self.pool.get('l10n_br_tax.estimate')
            date = datetime.now().strftime('%Y-%m-%d')
            tax_estimate_ids = obj_tax_estimate.search(
                cr, uid, [('fiscal_classification_id', '=',
                           product.fiscal_classification_id.id),
                          '|', ('date_start', '=', False),
                          ('date_start', '<=', date),
                          '|', ('date_end', '=', False),
                          ('date_end', '>=', date),
                          ('active', '=', True)])

            if tax_estimate_ids:
                tax_estimate = obj_tax_estimate.browse(
                    cr, uid, tax_estimate_ids)[0]
                tax_estimate_percent = 0.00
                if product.origin in ('1', '2', '6', '7'):
                    tax_estimate_percent += tax_estimate.federal_taxes_import
                else:
                    tax_estimate_percent += tax_estimate.federal_taxes_national

                tax_estimate_percent += tax_estimate.state_taxes
                tax_estimate_percent /= 100
                total_taxes = ((result['total_included'] - totaldc) *
                               tax_estimate_percent)
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
            product=product, partner=partner, force_excluded=force_excluded,
            fiscal_position=fiscal_position, insurance_value=insurance_value,
            freight_value=freight_value, other_costs_value=other_costs_value,
            base_tax=base_tax)
