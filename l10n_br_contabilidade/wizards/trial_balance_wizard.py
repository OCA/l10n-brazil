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


class AccountTrialBalanceWizard(models.TransientModel):
    """Will launch trial balance report and pass required args"""

    _inherit = "trial.balance.webkit"

    # pylint: disable=old-api7-method-defined
    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.abgf_account_report_trial_balance',
                'datas': data}
