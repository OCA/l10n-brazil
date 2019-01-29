# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'general.ledger.webkit'

    @api.multi
    def _print_report(self, data):
        data = super(AccountReportGeneralLedgerWizard, self)._print_report(data)
        data['report_name'] = 'account.abgf_account_report_general_ledger'

        return data
