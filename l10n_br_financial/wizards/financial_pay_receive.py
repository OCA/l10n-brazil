# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialPayreceive(models.TransientModel):

    _name = 'financial.pay_receive'

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
        # required=True
    )
    desconto = fields.Monetary()
    juros = fields.Monetary()
    multa = fields.Monetary()
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )

    @api.model
    def default_get(self, vals):
        res = super(FinancialPayreceive, self).default_get(vals)
        active_id = self.env.context.get('active_id')
        if (self.env.context.get('active_model') == 'financial.move' and
                active_id):
            fm = self.env['financial.move'].browse(active_id)
            res['currency_id'] = fm.currency_id.id
            res['ammount_paid'] = fm.amount_residual
            res['payment_date'] = fields.Date.today()
        return res

    @api.multi
    def doit(self):
        for wizard in self:
            # TODO

            active_id = self._context['active_id']
            account_financial = self.env['financial.move']

            financial_to_pay = account_financial.browse(active_id)

            if financial_to_pay.move_type == 'p':
                payment_type = 'pp'
            else:
                payment_type = 'rr'

            account_financial.create({
                'company_id': 1,
                'amount_document': wizard.ammount_paid,
                'ref': financial_to_pay.ref,
                'ref_item': financial_to_pay.ref_item,
                'credit_debit_date': wizard.credit_debit_date,
                'payment_mode': wizard.payment_mode,
                'amount_discount': wizard.desconto,
                'amount_delay_fee': wizard.multa,
                'amount_interest': wizard.juros,
                'currency_id': wizard.currency_id.id,
                'document_date': fields.Date.today(),
                'payment_id': active_id,
                'move_type': payment_type,
                'partner_id': financial_to_pay.partner_id.id,
                'document_number': financial_to_pay.document_number,
                'due_date': fields.Date.today()

            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
