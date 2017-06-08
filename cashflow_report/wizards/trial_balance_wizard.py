# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api



retorno = {u'meses': [u'Junho2017', u'Julho2017', u'Agosto2017'], u'resumo': [[u'1', u'ATIVO ', 165553.0, 86763.0, 0.0], [u'2', u'PASSIVO', -12320.0, -42340.0, 0.0]], u'contas': [[u'1', u'ATIVO ', 165553.0, 86763.0, 0.0], [u'1.1', u'CIRCULANTE', 165553.0, 86763.0, 0.0], [u'1.1.1', u'DISPON\xcdVEL', 165553.0, 86763.0, 0.0], [u'1.1.1.2', u'BANCOS CONTA MOVIMENTO', 165553.0, 86763.0, 0.0], [u'1.1.1.2.01', u'Banco \u201cexemplo\u201d', 165553.0, 86763.0, 0.0], [u'2', u'PASSIVO', -12320.0, -42340.0, 0.0], [u'2.1', u'CIRCULANTE', -12320.0, -42340.0, 0.0], [u'2.1.1', u'CONTAS A PAGAR', -12320.0, -42340.0, 0.0], [u'2.1.1.1', u'SAL\xc1RIOS A PAGAR', -12320.0, -42340.0, 0.0], [u'2.1.1.1.02', u'F\xe9rias a Pagar', -42340.0, 0.0, 0.0], [u'2.1.1.1.03', u'13\xba Sal\xe1rio a Pagar', -12320.0, 0.0, 0.0]]}



class TrialBalanceReportWizard(models.TransientModel):
    """Trial balance report wizard."""

    _name = "trial.balance.report.wizard"
    _description = "Trial Balance Report Wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    # date_range_id = fields.Many2one(
    #     comodel_name='date.range',
    #     required=True,
    #     string='Date range'
    # )

    date_from = fields.Date(required=True, default=fields.Date.today,)
    date_to = fields.Date(required=True, default=fields.Date.today,)
    # fy_start_date = fields.Date(required=True)

    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='all')

    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )

    hide_account_balance_at_0 = fields.Boolean(
        string='Hide account ending balance at 0',
        help='Use this filter to hide an account or a partner '
             'with an ending balance at 0. '
             'If partners are filtered, '
             'debits and credits totals will not match the trial balance.'
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    show_partner_details = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(
        readonly=True,
        default=False,
        string='Not only one unaffected earnings account'
    )

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     """Handle company change."""
    #     account_type = self.env.ref('account.data_unaffected_earnings')
    #     count = self.env['account.account'].search_count(
    #         [
    #             ('user_type_id', '=', account_type.id),
    #             ('company_id', '=', self.company_id.id)
    #         ])
    #     self.not_only_one_unaffected_earnings_account = count != 1

    # @api.onchange('date_range_id')
    # def onchange_date_range_id(self):
    #     """Handle date range change."""
    #     self.date_from = self.date_range_id.date_start
    #     self.date_to = self.date_range_id.date_end
    #     if self.date_from:
    #         self.fy_start_date = self.env.user.company_id.find_daterange_fy(
    #             fields.Date.from_string(self.date_range_id.date_start)
    #         ).date_start

    # @api.onchange('receivable_accounts_only', 'payable_accounts_only')
    # def onchange_type_accounts_only(self):
    #     """Handle receivable/payable accounts only change."""
    #     if self.receivable_accounts_only or self.payable_accounts_only:
    #         domain = []
    #         if self.receivable_accounts_only and self.payable_accounts_only:
    #             domain += [('internal_type', 'in', ('receivable', 'payable'))]
    #         elif self.receivable_accounts_only:
    #             domain += [('internal_type', '=', 'receivable')]
    #         elif self.payable_accounts_only:
    #             domain += [('internal_type', '=', 'payable')]
    #         self.account_ids = self.env['account.account'].search(domain)
    #     else:
    #         self.account_ids = None
    #
    # @api.onchange('show_partner_details')
    # def onchange_show_partner_details(self):
    #     """Handle partners change."""
    #     if self.show_partner_details:
    #         self.receivable_accounts_only = self.payable_accounts_only = True
    #     else:
    #         self.receivable_accounts_only = self.payable_accounts_only = False

    # @api.multi
    # def button_export_pdf(self):
    #     self.ensure_one()
    #     return self._export()

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        return self._export(xlsx_report=True)

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_balance_at_0': self.hide_account_balance_at_0,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            # 'fy_start_date': self.fy_start_date,
            'show_partner_details': self.show_partner_details,
            # 'fluxo_de_caixa': retorno,
        }

    def _export(self, xlsx_report=False):
        """Default export is PDF."""
        model = self.env['report_cashflow_qweb']
        report = model.create(self._prepare_report_trial_balance())
        return \
            report.with_context(fluxo_de_caixa=retorno).print_report(xlsx_report)
