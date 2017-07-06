# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    payment_mode_id = fields.Many2one(
        string="Payment Mode",
        comodel_name='payment.mode',
        # domain="[('type', '=', type)]"
    )

    payment_line_ids = fields.One2many(
        string="Orderns de Pagamento",
        comodel_name="payment.line",
        inverse_name="payslip_id",
    )

    def _compute_set_employee_id(self):
        super(HrPayslip, self)._compute_set_employee_id()
        print ('Ajuste o tipo de pagamento')
        for record in self:
            if record.contract_id:
                partner_id = \
                    record.contract_id.employee_id.parent_id.user_id.partner_id
                record.payment_mode_id = partner_id.supplier_payment_mode

        # self, type, partner_id, date_invoice=False,
        #     payment_term=False, partner_bank_id=False, company_id=False):
        # res = super(HrPayslip, self).onchange_partner_id(
        #     type, partner_id, date_invoice=date_invoice,
        #     payment_term=payment_term, partner_bank_id=partner_bank_id,
        #     company_id=company_id)
        # if partner_id:
        #     partner = self.env['res.partner'].browse(partner_id)
        #     if type == 'in_invoice':
        #         res['value']['payment_mode_id'] = \
        #             partner.supplier_payment_mode.id
        #     elif type == 'out_invoice':
        #         res['value']['payment_mode_id'] = \
        #             partner.customer_payment_mode.id
        #         # Do not change the default value of partner_bank_id if
        #         # partner.customer_payment_mode is False
        #         if partner.customer_payment_mode.bank_id:
        #             res['value']['partner_bank_id'] = \
        #                 partner.supplier_payment_mode.bank_id.id
        # else:
        #     res['value']['payment_mode_id'] = False
        # return res

    def create_payorder(self, mode_payment):
        '''
        Cria um payment order com base no metodo de pagamento
        :param mode_payment: 
        :return: 
        '''
        payment_order_model = self.env['payment.order']
        vals = {'mode': mode_payment.id,}
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
            # 'partner_bank_id': self.partner_bank_id.id,
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

        result_payorder_ids = []
        action_payment_type = 'debit'

        for holerite in self:
            if holerite.state != 'done':
                raise UserError(_(
                    "The payslip %s is not in Open state") %
                                holerite.contract_id.nome_do_contrato)
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

                    if not holerite.contract_id.employee_id.user_id.partner_id:
                        raise UserError(_(
                            "Nenhum partner associado com o employee %s") %
                                holerite.contract_id.employee_id.display_name)

                    self.create_payment_order_line(
                        payorder, rubrica.total, 'SALARIO ' + holerite.data_mes_ano,
                        holerite.contract_id.employee_id.address_home_id)
