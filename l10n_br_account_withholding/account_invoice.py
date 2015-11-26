# -*- encoding: utf-8 -*-
# #############################################################################
#
# Copyright (C) 2014 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import Warning

FIELD_STATE = {'draft': [('readonly', False)]}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.depends('invoice_line', 'tax_line.amount')
    def _amount_all(self):
        for inv in self:
            inv.amount_services = sum(
                line.price_total for line in inv.invoice_line)
            inv.issqn_base = sum(line.issqn_base for line in inv.invoice_line)
            inv.issqn_value = sum(
                line.issqn_value for line in inv.invoice_line)
            inv.service_pis_value = sum(
                line.pis_value for line in inv.invoice_line)
            inv.service_cofins_value = sum(
                line.cofins_value for line in inv.invoice_line)
            inv.csll_base = sum(line.csll_base for line in inv.invoice_line)
            inv.csll_value = sum(line.csll_value for line in inv.invoice_line)
            inv.ir_base = sum(line.ir_base for line in inv.invoice_line)
            inv.ir_value = sum(line.ir_value for line in inv.invoice_line)

            inv.amount_total = inv.amount_tax + \
                inv.amount_untaxed + inv.amount_services

            inv.amount_wh = inv.issqn_value_wh + inv.pis_value_wh + \
                                inv.cofins_value_wh + inv.csll_value_wh + \
                                inv.irrf_value_wh + inv.inss_value_wh

    issqn_wh = fields.Boolean(
        u'Retém ISSQN', readonly=True, states=FIELD_STATE)

    issqn_value_wh = fields.Float(
        u'Valor da retenção do ISSQN', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    pis_wh = fields.Boolean(
        u'Retém PIS', readonly=True, states=FIELD_STATE)

    pis_value_wh = fields.Float(
        u'Valor da retenção do PIS', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    cofins_wh = fields.Boolean(
        u'Retém COFINS', readonly=True, states=FIELD_STATE)

    cofins_value_wh = fields.Float(
        u'Valor da retenção do Cofins', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    csll_wh = fields.Boolean(
        u'Retém CSLL', readonly=True, states=FIELD_STATE)

    csll_value_wh = fields.Float(
        u'Valor da retenção de CSLL', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    irrf_wh = fields.Boolean(
        u'Retém IRRF', readonly=True, states=FIELD_STATE)

    irrf_base_wh = fields.Float(
        u'Base de calculo retenção do IRRF', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    irrf_value_wh = fields.Float(
        u'Valor da retenção de IRRF', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    inss_wh = fields.Boolean(
        u'Retém INSS', readonly=True, states=FIELD_STATE)

    inss_base_wh = fields.Float(
        u'Base de Cálculo da Retenção da Previdência Social', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    inss_value_wh = fields.Float(
        u'Valor da Retenção da Previdência Social ', readonly=True,
        states=FIELD_STATE, digits_compute=dp.get_precision('Account'))

    csll_base = fields.Float(
        string=u'Base CSLL', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    csll_value = fields.Float(
        string=u'Valor CSLL', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    ir_base = fields.Float(
        string=u'Base IR', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    ir_value = fields.Float(
        string=u'Valor IR', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    issqn_base = fields.Float(
        string=u'Base de Cálculo do ISSQN', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    issqn_value = fields.Float(
        string=u'Valor do ISSQN', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    service_pis_value = fields.Float(
        string=u'Valor do Pis sobre Serviços', compute='_amount_all',
        digits_compute=dp.get_precision('Account'), store=True)
    service_cofins_value = fields.Float(
        string=u'Valor do Cofins sobre Serviços', compute='_amount_all',
        store=True, digits_compute=dp.get_precision('Account'))
    amount_services = fields.Float(
        string=u'Total dos serviços', compute='_amount_all', store=True,
        digits_compute=dp.get_precision('Account'))
    amount_wh = fields.Float(
        string=u'Total de retenção', compute='_amount_all', store=True,
        digits_compute=dp.get_precision('Account'))

    def _whitholding_map(self, cr, uid, result, context=None, **kwargs):
        if not context:
            context = {}

        obj_partner = self.pool.get('res.partner').browse(
            cr, uid, kwargs.get('partner_id', False))
        obj_company = self.pool.get('res.company').browse(
            cr, uid, kwargs.get('company_id', False))

        result['value'][
            'issqn_wh'] = obj_company.issqn_wh or obj_partner.partner_fiscal_type_id.issqn_wh
        result['value'][
            'inss_wh'] = obj_company.inss_wh or obj_partner.partner_fiscal_type_id.inss_wh
        result['value'][
            'pis_wh'] = obj_company.pis_wh or obj_partner.partner_fiscal_type_id.pis_wh
        result['value'][
            'cofins_wh'] = obj_company.cofins_wh or obj_partner.partner_fiscal_type_id.cofins_wh
        result['value'][
            'csll_wh'] = obj_company.csll_wh or obj_partner.partner_fiscal_type_id.csll_wh
        result['value'][
            'irrf_wh'] = obj_company.irrf_wh or obj_partner.partner_fiscal_type_id.irrf_wh

        return result

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):

        result = super(AccountInvoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id, fiscal_category_id)

        return self._whitholding_map(
            cr, uid, result, False, partner_id=partner_id,
            partner_invoice_id=partner_id, company_id=company_id,
            fiscal_category_id=fiscal_category_id)

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        invoice_browse = self
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)

        move_debit = {'analytic_account_id': None, 'tax_code_id': 10, 'analytic_lines': [], 'tax_amount': 10,
                      'name': u'IR Recuperar 1.05% (Retenção)', 'ref': False, 'currency_id': False, 'credit': False,
                      'product_id': False, 'date_maturity': False, 'debit': 10, 'date': '2015-11-20',
                      'amount_currency': 0, 'product_uom_id': False, 'quantity': 1, 'partner_id': 17, 'account_id': 123}
        # for move in move_lines:
        #    print move
        #move_lines.append((0, 0, move_credit))
        move_lines.append((0, 0, move_debit))
        for move in move_lines:
            if move[2]['date_maturity']:
                move[2]['debit'] = move[2]['debit'] - 10

        # veriricar se o cliente x empresa retem o imposto e chamar o metodo
        # correspondente
        for invoice in self:
            self._compute_wh(invoice_browse)
        return move_lines

    def _compute_wh(self, invoice_browse):
        period_obj = self.env['account.period']
        line_obj = self.env['account.invoice.line']

        # if invoice_browse.company_id.wh_type == '1':
        #    raise Warning("Atenção!", "Regime de Caixa não implementado")
        # elif invoice_browse.company_id.wh_type == '2':

        date_invoice = invoice_browse.date_invoice
        if not date_invoice:
            date_invoice = time.strftime('%Y-%m-%d')
        result = {
            'pis_value_wh': 0.00,
            'cofins_value_wh': 0.00,
            'csll_value_wh': 0.00,
            'irrf_value_wh': 0.00,
            'issqn_value_wh': 0.00,
        }
        witholded = {
            'pis_value_wh': 0.00,
            'cofins_value_wh': 0.00,
            'csll_value_wh': 0.00,
            'irrf_value_wh': 0.00,
            'issqn_value_wh': 0.00,
            'irrf_base_wh': 0.00,
        }
        invoice = {
            'pis': 0.00,
            'cofins': 0.00,
            'csll': 0.00,
            'ir': 0.00,
        }
        previous = {
            'pis': 0.00,
            'cofins': 0.00,
            'csll': 0.00,
            'ir': 0.00,
        }
        amount_previous = 0.00

        for current_line in invoice_browse.invoice_line:
            if current_line.product_type == 'service':
                invoice['pis'] += current_line.pis_value
                invoice['cofins'] += current_line.cofins_value
                invoice['csll'] += current_line.csll_value
                invoice['ir'] += current_line.ir_value

       # PIS / COFINS / CSLL
        if (amount_previous +
                invoice_browse.amount_total) > invoice_browse.company_id.cofins_csll_pis_wh_base:
            if invoice_browse.pis_wh:
                result['pis_value_wh'] = invoice['pis'] + previous['pis']
            if invoice_browse.cofins_wh:
                result['cofins_value_wh'] = invoice[
                    'cofins'] + previous['cofins']
            if invoice_browse.csll_wh:
                result['csll_value_wh'] = invoice['csll'] + previous['csll']

        # IR: Existem divergencias entre as normativas verificar melhor a legislação
        # Pode ser que o total deva acumular para os proximos meses.
        if invoice_browse.irrf_wh:
            irrf_base = amount_previous + invoice_browse.amount_total
            irrf_value_wh = irrf_base * \
                invoice_browse.partner_id.partner_fiscal_type_id.irrf_wh_percent / \
                100
            if irrf_value_wh > invoice_browse.company_id.irrf_wh_base:
                result['irrf_value_wh'] = irrf_value_wh
                result['irrf_base_wh'] = irrf_base

        # INSS
        if invoice_browse.inss_wh:
            pass
            # TODO

        invoice_browse.write(result)

    # def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
    #     total, total_currency, invoice_move_lines = super(AccountInvoice, self).compute_invoice_totals(cr, uid, inv,
    #                                                                                                    company_currency,
    #                                                                                                    ref,
    #                                                                                                    invoice_move_lines,
    #                                                                                                    context=None)
    #     return total, total_currency, invoice_move_lines


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    csll_base = fields.Float('Base CSLL', required=True,
                             digits_compute=dp.get_precision('Account'), default=0.0)
    csll_value = fields.Float('Valor CSLL', required=True,
                              digits_compute=dp.get_precision('Account'), default=0.0)
    csll_percent = fields.Float('Perc CSLL', required=True,
                                digits_compute=dp.get_precision('Discount'), default=0.0)
    ir_base = fields.Float('Base IR', required=True,
                           digits_compute=dp.get_precision('Account'), default=0.0)
    ir_value = fields.Float('Valor IR', required=True,
                            digits_compute=dp.get_precision('Account'), default=0.0)
    ir_percent = fields.Float('Perc IR', required=True,
                              digits_compute=dp.get_precision('Discount'), default=0.0)

    def _amount_tax_csll(self, cr, uid, tax=False):
        print "chamou"
        result = {
            'csll_base': tax.get('total_base', 0.0),
            'csll_value': tax.get('amount', 0.0),
            'csll_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_ir(self, cr, uid, tax=False):
        result = {
            'ir_base': tax.get('total_base', 0.0),
            'ir_value': tax.get('amount', 0.0),
            'ir_percent': tax.get('percent', 0.0) * 100,
        }
        return result

#
#     # _columns = {
#     # TODO: Implmentar o calculo de retenção de ISS que varia por item.
#     # }
#
#     def fields_view_get(self, cr, uid, view_id=None, view_type=False,
#                         context=None, toolbar=False, submenu=False):
#         result = super(AccountInvoiceLine, self).fields_view_get(
#             cr, uid, view_id=view_id, view_type=view_type, context=context,
#             toolbar=toolbar, submenu=submenu)
#
#         return result
#
#     def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='',
#                           type='out_invoice', partner_id=False,
#                           fposition_id=False, price_unit=False,
#                           currency_id=False, context=None, company_id=False,
#                           parent_fiscal_category_id=False,
#                           parent_fposition_id=False):
#         result = super(AccountInvoiceLine, self).product_id_change(
#             cr, uid, ids, product, uom, qty, name, type, partner_id,
#             fposition_id, price_unit, currency_id, context, company_id,
#             parent_fiscal_category_id, parent_fposition_id)
#
#         return result
#
#
# class AccountInvoiceTax(orm.Model):
#     _inherit = 'account.invoice.tax'
#
#     def move_line_get(self, cr, uid, invoice_id):
#         res = super(AccountInvoiceTax, self).move_line_get(cr, uid, invoice_id)
#         return res
