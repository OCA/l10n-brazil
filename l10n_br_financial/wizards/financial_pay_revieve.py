# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FinancialPay_revieve(models.TransientModel):

    _name = 'financial.pay_revieve'
    valor_pago = fields.Float()

    name = fields.Char()

    @api.multi
    def doit(self):
        for wizard in self:
            # TODO

            active_id = self._context['active_id']
            account_financial = self.env['financial.move']

            financial_to_pay = account_financial.browse(active_id)

            if financial_to_pay.type == 'p':
                payment_type = 'pp'
            else:
                payment_type = 'rr'



            account_financial.create({
                'currency_id': 1,
                'company_id': 1,
                'amount_document': wizard.valor_pago,
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



