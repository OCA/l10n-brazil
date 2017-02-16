# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FinancialPay_revieve(models.TransientModel):

    _name = 'financial.pay_revieve'
    ammount_paid = fields.Monetary(
        required=True
    )

    ref = fields.Char()
    payment_date = fields.Date(
        required=True
    )
    credit_debit_date = fields.Date(
        readonly=True
    )
    payment_mode = fields.Many2one(
        comodel_name='payment.mode',
        #required=True
    )
    desconto = fields.Monetary()
    juros = fields.Monetary()
    multa = fields.Monetary()
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )

    @api.multi
    def doit(self):
        for wizard in self:
            #TODO

            active_id = self._context['active_id']
            account_financial = self.env['financial.move']

            financial_to_pay = account_financial.browse(active_id)

            if financial_to_pay.type == 'p':
                payment_type = 'pp'
            else:
                payment_type = 'rr'



            account_financial.create({
                'company_id': 1,
                'amount_document': wizard.ammount_paid,
                'ref': wizard.ref,
                'credit_debit_date': wizard.credit_debit_date,
                'payment_mode': wizard.payment_mode,
                'amount_discount': wizard.desconto,
                'amount_delay_fee': wizard.multa,
                'amount_interest': wizard.juros,
                'currency_id': wizard.currency_id.id,
                'payment_id': active_id,
                'type': payment_type,
            })

        # action = {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Action Name',  # TODO
        #     'res_model': 'result.model',  # TODO
        #     'domain': [('id', '=', result_ids)],  # TODO
        #     'view_mode': 'form,tree',
        # }
        # return action
        return True



