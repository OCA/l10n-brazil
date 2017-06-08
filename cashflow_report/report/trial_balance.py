# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class TrialBalanceReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * TrialBalanceReport
    ** TrialBalanceReportAccount
    *** TrialBalanceReportPartner
            If "show_partner_details" is selected
    """

    _name = 'report_cashflow_qweb'

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()

    # fy_start_date = fields.Date()
    only_posted_moves = fields.Boolean()
    hide_account_balance_at_0 = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    show_partner_details = fields.Boolean()
    # fluxo_de_caixa = fields.Text(
    #     string='Dicionario com o fluxo de caixa ja processado',
    # )


    # General Ledger Report Data fields,
    # used as base for compute the data reports
    # general_ledger_id = fields.Many2one(
    #     comodel_name='report_general_ledger_qweb'
    # )

    # Data fields, used to browse report data
    # account_ids = fields.One2many(
    #     comodel_name='report_trial_balance_qweb_account',
    #     inverse_name='report_id'
    # )


class TrialBalanceReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_cashflow_qweb'

    @api.multi
    def print_report(self, xlsx_report=False):
        self.ensure_one()
        # self.compute_data_for_report()
        if xlsx_report:
            report_name = 'cashflow_report.' \
                          'report_trial_balance_xlsx'

        return self.env['report'].get_action(docids=self.ids,
                                             report_name=report_name)

#     def _prepare_report_general_ledger(self):
#         self.ensure_one()
#         return {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#             'only_posted_moves': self.only_posted_moves,
#             'hide_account_balance_at_0': self.hide_account_balance_at_0,
#             'company_id': self.company_id.id,
#             'filter_account_ids': [(6, 0, self.filter_account_ids.ids)],
#             'filter_partner_ids': [(6, 0, self.filter_partner_ids.ids)],
#             # 'fy_start_date': self.fy_start_date,
#         }
#
#     @api.multi
#     def compute_data_for_report(self):
#         self.ensure_one()
#         # Compute General Ledger Report Data.
#         # The data of Trial Balance Report
#         # are based on General Ledger Report data.
#         # model = self.env['report_general_ledger_qweb']
#         # self.general_ledger_id = model.create(
#         #     self._prepare_report_general_ledger()
#         # )
#         # self.general_ledger_id.compute_data_for_report(
#         #     with_line_details=False, with_partners=self.show_partner_details
#         # )
#         #
#         # # Compute report data
#         # self._inject_account_values()
#         # if self.show_partner_details:
#         #     self._inject_partner_values()
#         # # Refresh cache because all data are computed with SQL requests
#         # self.refresh()
#
#     def _inject_account_values(self):
#         """Inject report values for report_trial_balance_qweb_account"""
#         query_inject_account = """
# INSERT INTO
#     report_trial_balance_qweb_account
#     (
#     report_id,
#     create_uid,
#     create_date,
#     account_id,
#     code,
#     name,
#     initial_balance,
#     debit,
#     credit,
#     final_balance
#     )
# SELECT
#     %s AS report_id,
#     %s AS create_uid,
#     NOW() AS create_date,
#     rag.account_id,
#     rag.code,
#     rag.name,
#     rag.initial_balance AS initial_balance,
#     rag.final_debit - rag.initial_debit AS debit,
#     rag.final_credit - rag.initial_credit AS credit,
#     rag.final_balance AS final_balance
# FROM
#     report_general_ledger_qweb_account rag
# WHERE
#     rag.report_id = %s
#         """
#         query_inject_account_params = (
#             self.id,
#             self.env.uid,
#             self.general_ledger_id.id,
#         )
#         self.env.cr.execute(query_inject_account, query_inject_account_params)
#
#     def _inject_partner_values(self):
#         """Inject report values for report_trial_balance_qweb_partner"""
#         query_inject_partner = """
# INSERT INTO
#     report_trial_balance_qweb_partner
#     (
#     report_account_id,
#     create_uid,
#     create_date,
#     partner_id,
#     name,
#     initial_balance,
#     debit,
#     credit,
#     final_balance
#     )
# SELECT
#     ra.id AS report_account_id,
#     %s AS create_uid,
#     NOW() AS create_date,
#     rpg.partner_id,
#     rpg.name,
#     rpg.initial_balance AS initial_balance,
#     rpg.final_debit - rpg.initial_debit AS debit,
#     rpg.final_credit - rpg.initial_credit AS credit,
#     rpg.final_balance AS final_balance
# FROM
#     report_general_ledger_qweb_partner rpg
# INNER JOIN
#     report_general_ledger_qweb_account rag ON rpg.report_account_id = rag.id
# INNER JOIN
#     report_trial_balance_qweb_account ra ON rag.code = ra.code
# WHERE
#     rag.report_id = %s
# AND ra.report_id = %s
#         """
#         query_inject_partner_params = (
#             self.env.uid,
#             self.general_ledger_id.id,
#             self.id,
#         )
#         self.env.cr.execute(query_inject_partner, query_inject_partner_params)
