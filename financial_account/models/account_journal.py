# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

JOURNAL_FINANCIAL_INTEGRATION = {
    'sale': True,
    'purchase': True,
}


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    @api.depends('type')
    @api.multi
    def _compute_financial_integration(self):
        for record in self:
            record.financial_integration = JOURNAL_FINANCIAL_INTEGRATION.get(
                record.type, False
            )

    financial_integration = fields.Boolean(
        string=u'Integration with financial',
        compute='_compute_financial_integration',
        store=True,
    )
