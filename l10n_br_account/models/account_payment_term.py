# Copyright 2020 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.payment.term'

    @api.one
    def compute(self, value, date_ref=False):
        financial_ids = self.env.context.get('financial_ids')
        if financial_ids:
            return [(x.date_maturity, x.amount) for x in financial_ids]
        result = super(AccountInvoice, self).compute(value, date_ref)
        return result[0]
