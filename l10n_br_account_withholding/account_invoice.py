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


from openerp import api, fields, models
from openerp.addons import decimal_precision as dp

FIELD_STATE = {'draft': [('readonly', False)]}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.depends('invoice_line', 'tax_line.amount')
    def _amount_all_service(self):
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
            inv.inss_base = sum(line.inss_base for line in inv.invoice_line)
            inv.inss_value = sum(line.inss_value for line in inv.invoice_line)

            inv.amount_total = inv.amount_tax + \
                inv.amount_untaxed
            inv.amount_wh = inv.issqn_value_wh + inv.pis_value_wh + \
                inv.cofins_value_wh + inv.csll_value_wh + \
                inv.irrf_value_wh + inv.inss_value_wh

    @api.multi
    @api.depends('amount_total', 'amount_wh')
    def _amount_net(self):
        for inv in self:
            inv.amount_net = inv.amount_total - inv.amount_wh

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
        string=u'Base CSLL', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    csll_value = fields.Float(
        string=u'Valor CSLL', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    ir_base = fields.Float(
        string=u'Base IR', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    ir_value = fields.Float(
        string=u'Valor IR', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    issqn_base = fields.Float(
        string=u'Base de Cálculo do ISSQN', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    issqn_value = fields.Float(
        string=u'Valor do ISSQN', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    inss_base = fields.Float(
        string=u'Valor do INSS', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    inss_value = fields.Float(
        string=u'Valor do INSS', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    service_pis_value = fields.Float(
        string=u'Valor do Pis sobre Serviços', compute='_amount_all_service',
        digits_compute=dp.get_precision('Account'), store=True)
    service_cofins_value = fields.Float(
        string=u'Valor do Cofins sobre Serviços',
        compute='_amount_all_service',
        store=True, digits_compute=dp.get_precision('Account'))
    amount_services = fields.Float(
        string=u'Total dos serviços', compute='_amount_all_service',
        store=True, digits_compute=dp.get_precision('Account'))
    amount_wh = fields.Float(
        string=u'Total de retenção', compute='_amount_all_service', store=True,
        digits_compute=dp.get_precision('Account'))
    amount_net = fields.Float(
        string=u'Total Líquido', compute='_amount_net',
        digits_compute=dp.get_precision('Account'))

    def whitholding_map(self, cr, uid, **kwargs):
        result = {}
        obj_partner = self.pool.get('res.partner').browse(
            cr, uid, kwargs.get('partner_id', False))
        obj_company = self.pool.get('res.company').browse(
            cr, uid, kwargs.get('company_id', False))

        result['issqn_wh'] = obj_company.issqn_wh or \
            obj_partner.partner_fiscal_type_id.issqn_wh
        result['inss_wh'] = obj_company.inss_wh or \
            obj_partner.partner_fiscal_type_id.inss_wh
        result['pis_wh'] = obj_company.pis_wh or \
            obj_partner.partner_fiscal_type_id.pis_wh
        result['cofins_wh'] = obj_company.cofins_wh or \
            obj_partner.partner_fiscal_type_id.cofins_wh
        result['csll_wh'] = obj_company.csll_wh or \
            obj_partner.partner_fiscal_type_id.csll_wh
        result['irrf_wh'] = obj_company.irrf_wh or \
            obj_partner.partner_fiscal_type_id.irrf_wh

        return result

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False,
                            fiscal_category_id=False):

        result = super(AccountInvoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id, fiscal_category_id)

        result['value'].update(self.whitholding_map(
            cr, uid, partner_id=partner_id, company_id=company_id))

        return result

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)

        self.compute_with_holding()

        # What we do here? IMPORTANT
        # We make a copy of the retention tax and calculate the new total
        # in the payment lines
        value_to_debit = 0.0
        move_lines_new = []
        move_lines_tax = [move for move in move_lines
                          if not move[2]['product_id']
                          and not move[2]['date_maturity']]
        move_lines_payment = [move for move in move_lines
                              if not move[2]['product_id']
                              and move[2]['date_maturity']]
        move_lines_products = [move for move in move_lines
                               if move[2]['product_id']
                               and not move[2]['date_maturity']]

        move_lines_new.extend(move_lines_products)

        def copy_move(move):
            copy = (0, 0, move[2].copy())
            copy[2]['debit'] = move[2]['credit']
            copy[2]['credit'] = move[2]['debit']
            copy[2]['name'] = copy[2]['name'] + u'- Retenção'
            return copy

        for move in move_lines_tax:
            move_lines_new.append(move)

            tax_code = self.env['account.tax.code'].browse(
                move[2]['tax_code_id'])

            if tax_code.domain == 'issqn' and self.issqn_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

            if tax_code.domain == 'pis' and self.pis_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

            if tax_code.domain == 'cofins' and self.cofins_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

            if tax_code.domain == 'inss' and self.inss_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

            if tax_code.domain == 'csll' and self.csll_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

            if tax_code.domain == 'irpj' and self.irrf_wh:
                value_to_debit += move[2]['credit'] or move[2]['debit']
                move_lines_new.append(copy_move(move))

        move_lines_new.extend(move_lines_payment)

        if value_to_debit > 0.0:
            value_item = value_to_debit / float(len(move_lines_payment))
            for move in move_lines_payment:
                if move[2]['debit']:
                    move[2]['debit'] = move[2]['debit'] - value_item
                elif move[2]['credit']:
                    move[2]['credit'] = move[2]['credit'] - value_item

        return move_lines_new

    @api.multi
    def compute_with_holding(self):
        for inv in self:
            if inv.pis_value > inv.company_id.cofins_csll_pis_wh_base and \
               inv.pis_wh:
                inv.pis_value_wh = inv.pis_value
            else:
                inv.pis_wh = False
                inv.pis_value_wh = 0.0

            if inv.cofins_value > inv.company_id.cofins_csll_pis_wh_base and \
               inv.cofins_wh:
                inv.cofins_value_wh = inv.cofins_value
            else:
                inv.cofins_wh = False
                inv.cofins_value_wh = 0.0

            if inv.csll_value > inv.company_id.cofins_csll_pis_wh_base and \
               inv.csll_wh:
                inv.csll_value_wh = inv.csll_value
            else:
                inv.csll_wh = False
                inv.csll_value_wh = 0.0

            if inv.issqn_wh:
                inv.issqn_value_wh = inv.issqn_value
            else:
                inv.issqn_value_wh = 0.0

            if inv.ir_value > inv.company_id.irrf_wh_base and inv.irrf_wh:
                inv.irrf_value_wh = inv.ir_value
                inv.irrf_base_wh = inv.ir_base
            else:
                inv.irrf_wh = False
                inv.irrf_value_wh = 0.0

            if inv.inss_value > inv.company_id.inss_wh_base and inv.inss_wh:
                inv.inss_base_wh = inv.inss_base
                inv.inss_value_wh = inv.inss_value
            else:
                inv.inss_wh = False
                inv.inss_value_wh = 0.0

            inv.amount_wh = inv.issqn_value_wh + inv.pis_value_wh + \
                inv.cofins_value_wh + inv.csll_value_wh + \
                inv.irrf_value_wh + inv.inss_value_wh


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    csll_base = fields.Float('Base CSLL', required=True,  default=0.0,
                             digits_compute=dp.get_precision('Account'))
    csll_value = fields.Float('Valor CSLL', required=True, default=0.0,
                              digits_compute=dp.get_precision('Account'))
    csll_percent = fields.Float('Perc CSLL', required=True, default=0.0,
                                digits_compute=dp.get_precision('Discount'))
    ir_base = fields.Float('Base IR', required=True, default=0.0,
                           digits_compute=dp.get_precision('Account'))
    ir_value = fields.Float('Valor IR', required=True, default=0.0,
                            digits_compute=dp.get_precision('Account'))
    ir_percent = fields.Float('Perc IR', required=True, default=0.0,
                              digits_compute=dp.get_precision('Discount'))
    inss_base = fields.Float('Base INSS', required=True, default=0.0,
                             digits_compute=dp.get_precision('Account'))
    inss_value = fields.Float('Valor INSS', required=True, default=0.0,
                              digits_compute=dp.get_precision('Account'))
    inss_percent = fields.Float('Perc. INSS', required=True, default=0.0,
                                digits_compute=dp.get_precision('Discount'))

    def _amount_tax_csll(self, cr, uid, tax=False):
        result = {
            'csll_base': tax.get('total_base', 0.0),
            'csll_value': tax.get('amount', 0.0),
            'csll_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_irpj(self, cr, uid, tax=False):
        result = {
            'ir_base': tax.get('total_base', 0.0),
            'ir_value': tax.get('amount', 0.0),
            'ir_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_inss(self, cr, uid, tax=False):
        result = {
            'inss_base': tax.get('total_base', 0.0),
            'inss_value': tax.get('amount', 0.0),
            'inss_percent': tax.get('percent', 0.0) * 100,
        }
        return result
