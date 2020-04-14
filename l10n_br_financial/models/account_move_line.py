# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    financial_payment_id = fields.Many2one(
        comodel_name='account.payment',
    )

    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        super(AccountMoveLine, self).reconcile(writeoff_acc_id, writeoff_journal_id)
        for record in self:
            if record.matched_debit_ids and record.financial_payment_id:
                record.matched_debit_ids.debit_move_id.payment_id.debt_id = record.financial_payment_id

            elif record.matched_credit_ids and record.financial_payment_id:
                record.matched_credit_ids.credit_move_id.payment_id.debt_id = record.financial_payment_id
