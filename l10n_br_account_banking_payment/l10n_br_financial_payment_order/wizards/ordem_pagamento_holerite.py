# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api, models, fields, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import MES_DO_ANO


class PayslipPaymentCreateOrder(models.Model):
    _name = "payslip.payment.order.create"

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )

    ano = fields.Integer(
        strin="Ano",
        default=datetime.now().year,
        required=True,
    )

    entries = fields.Many2many(
        comodel_name='hr.payslip',
        rel='payorder_line_payslip_rel',
        column1='pay_id',
        column2='payslip_id',
        string='Entries'
    )

    @api.multi
    def _buscar_holerites_com_conta_bancaria_contrato(self, payslip_ids):
        holerites = []
        for holerite in payslip_ids:
            if holerite.contract_id.conta_bancaria_id:
                holerites.append(holerite)
        return holerites

    @api.model
    def default_get(self, field_list):
        res = super(PayslipPaymentCreateOrder, self).default_get(field_list)
        context = self.env.context
        if ('entries' in field_list and context.get('payslip_id') and
                context.get('populate_results')):
            res.update({'entries': context['payslip_id']})
        return res

    @api.multi
    def buscar_linhas_holerites(self):
        payment_order = self.env['payment.order'].browse(
            self.env.context.get('active_id')
        )
        payslip_obj = self.env['hr.payslip']
        payslip_ids = payslip_obj.search(
            [
                ('tipo_de_folha', '=', payment_order.tipo_de_folha),
                ('mes_do_ano', '=', self.mes_do_ano),
                ('ano', '=', self.ano),
                ('state', '=', 'verify')
            ]
        )
        payslips_partner_bank_id = \
            self._buscar_holerites_com_conta_bancaria_contrato(payslip_ids)
        context = self.env.context.copy()
        context['payslip_id'] = []
        if payslips_partner_bank_id:
            context['payslip_id'] = [
                payslip.id for payslip in payslips_partner_bank_id
            ]
        context['populate_results'] = True
        model_data_obj = self.env['ir.model.data']
        model_datas = model_data_obj.search(
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'payslip_payment_lines_create_order_view')])
        return {'name': _('Entry Lines'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payslip.payment.order.create',
                'views': [(model_datas[0].res_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    @api.multi
    def _preparar_linha_do_holerite(self, payment, line):
        self.ensure_one()
        date_to_pay = False  # no payment date => immediate payment
        state = 'normal'
        communication = 'Holerite: ' + line.display_name or '-'
        amount_currency = line.total
        res = {
            'amount_currency': amount_currency,
            'bank_id': line.contract_id.conta_bancaria_id.id,
            'order_id': payment.id,
            'partner_id': line.partner_id and line.partner_id.id or False,
            # account banking
            'communication': communication,
            'state': state,
            # end account banking
            'date': date_to_pay,
            'payslip_id': line.slip_id.id,
        }
        return res

    @api.multi
    def _buscar_rubricas_a_pagar(self, payslip):
        rubricas = []
        for line in payslip.line_ids:
            if line.code in ['LIQUIDO', 'PENSAO_ALIMENTICIA']:
                rubricas.append(line)
        return rubricas

    @api.multi
    def create_payment(self):
        if not self.entries:
            return {'type': 'ir.actions.act_window_close'}
        context = self.env.context.copy()
        context['default_payment_order_type'] = 'payment'
        payment_line_obj = self.env['payment.line']
        payment = self.env['payment.order'].browse(context['active_id'])
        # Populate the current payment with new lines:
        for line in self.entries:
            linha_rubrica = self._buscar_rubricas_a_pagar(line)
            for rubrica in linha_rubrica:
                vals = self._preparar_linha_do_holerite(payment, rubrica)
                payment_line_obj.create(vals)
        # Force reload of payment order view as a workaround for lp:1155525
        return {'name': _('Payment Orders'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'payment.order',
                'res_id': context['active_id'],
                'type': 'ir.actions.act_window'}
