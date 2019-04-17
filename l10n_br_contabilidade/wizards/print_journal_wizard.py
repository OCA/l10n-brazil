# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'print.journal.webkit'

    account_depara_plano_id = fields.Many2one(
        string='Referência Plano de Contas',
        comodel_name='account.depara.plano',
    )

    exibe_criador_aprovador = fields.Boolean(
        string='Exibir criador e aprovador')

    @api.multi
    def _print_report(self, data):
        data['form']['account_depara_plano_id'] = \
            self.account_depara_plano_id.id
        data['form']['exibe_criador_aprovador'] = self.exibe_criador_aprovador
        data = self.pre_print_report(data)
        data = super(AccountReportGeneralLedgerWizard, self)._print_report(data)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.l10n_br_account_report_print_journal',
                'datas': data}
