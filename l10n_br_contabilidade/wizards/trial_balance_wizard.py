# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models


class AccountTrialBalanceWizard(models.TransientModel):
    _inherit = "trial.balance.webkit"

    lancamento_de_fechamento = fields.Boolean(
        string=u'Lançamentos de Fechamento',
        default=False,
    )

    @api.multi
    def _print_report(self, data):
        data['form']['lancamento_de_fechamento'] = self.lancamento_de_fechamento

        return super(AccountTrialBalanceWizard, self)._print_report(data)


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'general.ledger.webkit'

    def _print_report(self, cr, uid, ids, data, context=None):
        data = self.pre_print_report(cr, uid, ids, data, context=context)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.abgf_account_report_general_ledger',
                'datas': data}
