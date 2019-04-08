# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'general.ledger.webkit'

    coluna_saldo_periodo = fields.Boolean(
        string='Exibir coluna saldo no periodo',
        default=False,
    )

    @api.multi
    def _print_report(self, data):
        data['form']['coluna_saldo_periodo'] = self.coluna_saldo_periodo
        data['form']['target_move'] = self.target_move
        data = self.pre_print_report(data)
        data = super(AccountReportGeneralLedgerWizard, self)._print_report(data)

        if not self.env.context.get('xls_export'):
            data['report_name'] = \
                'account.l10n_br_account_report_general_ledger'

        return data
