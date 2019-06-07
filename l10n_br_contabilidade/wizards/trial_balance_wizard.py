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

    exibir_natureza = fields.Boolean(
        string=u'Exibir Natureza Conta?',
        default=False,
    )

    account_depara_plano_id = fields.Many2one(
        string='Referência Plano de Contas',
        comodel_name='account.depara.plano',
    )

    account_ids = fields.Many2many(
        comodel_name='account.account',
        domain="[('account_depara_plano_id', '=', account_depara_plano_id)]",
    )

    @api.onchange('account_depara_plano_id')
    def onchange_account_depara(self):
        """
        """
        for record in self:
            if record.account_depara_plano_id:
                record.chart_account_id = \
                    record.account_depara_plano_id.account_account_id

    @api.multi
    def _print_report(self, data):
        data['form']['lancamento_de_fechamento'] = \
            self.lancamento_de_fechamento
        data['form']['exibir_natureza'] = self.exibir_natureza
        data['form'][
            'account_depara_plano_id'] = self.account_depara_plano_id.id
        data['form']['account_depara_id'] = self.account_ids.ids
        data = self.pre_print_report(data)
        data = super(AccountTrialBalanceWizard, self)._print_report(data)

        if not self.env.context.get('xls_export'):
            data['report_name'] = \
                'account.l10n_br_account_report_trial_balance'

        return data
