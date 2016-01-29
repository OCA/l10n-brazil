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
from datetime import datetime, timedelta
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
                    ('debit', '>', 0),
                    ('account_id.type', '=', 'receivable'),
                ]
            # for i in domain:
            #     del i
            # tax_code_ids = self.env[
            #     'account.tax.code'].search([('domain', '=', 'icms')])

            # domain.append(('tax_code_id', 'in', tax_code_ids.ids))
        return True

    @api.multi
    def _prepare_payment_line(self, payment, line):
        res = super(PaymentOrderCreate, self)._prepare_payment_line(
            payment, line
        )
        if payment.mode.type.code == 'gnre':
            value = getattr(line.invoice, payment.mode.gnre_value_field.name)
            res['amount_currency'] = value
            res['date'] = line.invoice.date_invoice
            res['ml_maturity_date'] = (
                datetime.strptime(
                    line.invoice.date_invoice, "%Y-%m-%d") +
                timedelta(days=line.invoice.gnre_due_days))
        return res

    # @api.multi
    # def create_payment(self):
    #     super(PaymentOrderCreate, self).create_payment()
    #
    #     parser_gnre = bradesco_tax.BradescoGnre()
    #
    #     arq = open('/tmp/testeGNRE', 'w')
    #
    #     texto = ''
    #
    #     for line in self.entries:
    #         if line.partner_id.is_company:
    #             tipo_inscricao = '2'
    #         else:
    #             tipo_inscricao = '1'
    #
    #         if str(line.credit)[-2] == '.':
    #             valor_tributo = str(line.credit).replace('.', '') + '0'
    #
    #         endereco01 = str(line.partner_id.street)
    #         # endereco02 = str(line.partner_id.street2.replace('º', ''))
    #         endereco_cliente = endereco01
    #         vals = {
    #             'identificador_tributo': 'G',
    #             'nome_cliente': str(line.partner_id.name),
    #             'endereco_cliente': endereco_cliente,
    #             'cep_cliente': str(line.partner_id.zip.replace('-', '')),
    #             'uf_cliente': str(line.partner_id.state_id.code),
    #             'autoriza_pagamento': 'S',
    #             'tipo_inscricao': tipo_inscricao,
    #             'uf_favorecida': str(line.partner_id.state_id.code),
    #             'telefone_cliente': str(line.partner_id.phone
    #                                     .replace('(', '').replace(')', '')
    #                                     .replace('-', '').replace(' ', '')),
    #             'numero_inscricao': str(line.partner_id.cnpj_cpf
    #                                     .replace('.', '').replace('/', '')
    #                                     .replace('-', '')),
    #             'valor_do_principal': valor_tributo,
    #             'data_pagamento_tributo': line.date.replace('-', ''),
    #             'data_vencimento_tributo': line.date.replace('-', ''),
    #             'num_doc_origem': str(line.invoice.display_name),
    #         }
    #
    #         linha_arquivo = parser_gnre.remessa(**vals)
    #         texto += linha_arquivo
    #         texto += '\n'
    #         print linha_arquivo
    #
    #     arq.write(texto)
    #     arq.close()
    #
    #     return True




#
#
# class AccountInvoiceSeparetedTaxes(models.Model):
#     _inherit = 'account.invoice'
#
#     icms_st_value_total = fields.Float(
#         'Total de Subsituição Tributária antecipada em nome do cliente',
#         digits=dp.get_precision('Account'), default=0.00)
#     gerar_gnre = fields.Boolean("Gerar GNRE", related='partner_id.gerar_gnre',
#                                 store=True)

#     @api.multi
#     @api.depends('invoice_line', 'tax_line.amount')
#     def _compute_amount(self):
#         super(AccountInvoiceSeparetedTaxes, self)._compute_amount()
#
#         self.amount_total = self.amount_untaxed + \
#             self.amount_costs + self.amount_insurance + self.amount_freight
#
#         self.write({'icms_st_value_total': self.icms_st_value})
#
# class AccountInvoiceProductIcmsst(models.Model):
#     _inherit = 'account.invoice.line'
