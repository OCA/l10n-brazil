# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    payment_mode_id = fields.Many2one(
        string="Modo de Pagamento",
        comodel_name='payment.mode',
        domain="[('tipo_pagamento', '=', 'folha')]"
    )

    payment_order_id = fields.Many2one(
        string="Ordem de pagamento",
        comodel_name='payment.order',
        readonly=True,
        # domain="[('type', '=', type)]",
    )

    payment_line_ids = fields.One2many(
        string="Pagamentos",
        comodel_name="payment.line",
        inverse_name="payslip_id",
        readonly=True,
    )

    paid_order = fields.Boolean(
        string='Pago',
        compute='_compute_paid',
        readonly=True,
        store=True,
    )

    @api.multi
    def test_paid(self):
        if not self.payment_line_ids:
            return False
        for line in self.payment_line_ids:
            if not line.state2:
                return False
            if line.state2 != 'paid':
                return False
        return True

    @api.one
    @api.depends('payment_line_ids.bank_line_id.state2')
    def _compute_paid(self):
        self.paid_order = self.test_paid()

    def _compute_set_employee_id(self):
        """
        Setar a forma de pagamento no compute do holerite, buscando do contrato
        """
        super(HrPayslip, self)._compute_set_employee_id()
        for record in self:
            if record.contract_id:
                record.payment_mode_id = record.contract_id.payment_mode_id
                # partner_id = \
                #     record.contract_id.employee_id.parent_id.user_id.partner_id
                # record.payment_mode_id = partner_id.supplier_payment_mode

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        return True

    def create_payorder(self, mode_payment):
        '''
        Cria um payment order com base no metodo de pagamento
        :param mode_payment: Modo de pagamento
        :return: objeto do payment.order
        '''
        payment_order_model = self.env['payment.order']
        vals = {'mode': mode_payment.id, }
        return payment_order_model.create(vals)

    @api.multi
    def create_payment_order_line(
            self, payment_order, total, communication, partner_id):
        """
        Cria a linha da ordem de pagamento
        """
        payment_line_model = self.env['payment.line']
        vals = {
            'order_id': payment_order.id,
            'bank_id': self.contract_id.conta_bancaria_id.id,
            'partner_id': partner_id.id,
            # 'move_line_id': self.id,
            'communication': communication,
            # 'communication_type': communication_type,
            # 'currency_id': currency_id,
            'amount_currency': total,
            # date is set when the user confirms the payment order
            'payslip_id': self.id,
        }
        return payment_line_model.create(vals)

    @api.multi
    def create_payment_order(self):

        payment_order_model = self.env['payment.order']

        for holerite in self:
            if holerite.state != 'verify':
                raise UserError(_(
                    "The payslip %s is not in Open state") %
                    holerite.contract_id.nome_contrato)
            if not holerite.payment_mode_id:
                raise UserError(_(
                    "No Payment Mode on holerite %s") % holerite.number)

            # Buscar ordens de pagamento do mesmo tipo
            payorders = payment_order_model.search([
                ('mode', '=', holerite.payment_mode_id.id),
                ('state', '=', 'draft')]
            )

            if payorders:
                payorder = payorders[0]
            else:
                payorder = self.create_payorder(holerite.payment_mode_id)

            for rubrica in holerite.line_ids:
                if rubrica.code == 'LIQUIDO':
                    self.create_payment_order_line(
                        payorder, rubrica.total,
                        'SALARIO ' + holerite.data_mes_ano, rubrica.partner_id)

                if rubrica.code == 'PENSAO_ALIMENTICIA':
                    self.create_payment_order_line(
                        payorder, rubrica.total,
                        'PENSAO ALIMENTICIA ' + holerite.data_mes_ano,
                        rubrica.partner_id)
