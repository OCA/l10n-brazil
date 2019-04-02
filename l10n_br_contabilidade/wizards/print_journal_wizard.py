# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'print.journal.webkit'

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}

        data = self.pre_print_report(cursor, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.l10n_br_account_report_print_journal',
                'datas': data}
