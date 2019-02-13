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
        data['form']['lancamento_de_fechamento'] = \
            self.lancamento_de_fechamento
        data = self.pre_print_report(data)
        data = super(AccountTrialBalanceWizard, self)._print_report(data)

        if not self.env.context.get('xls_export'):
            data[
                'report_name'] = 'account.l10n_br_account_report_trial_balance'

        return data
