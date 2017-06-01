# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from .inherited_account_financial_report import REPORT_TYPE_SUMMARY


class ReportAccountReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def _compute_report_balance(self, reports):
        res = super(ReportAccountReportFinancial, self)._compute_report_balance(
            reports)

        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.type != REPORT_TYPE_SUMMARY:
                continue

            for summary in report.summary_report_ids:
                res_summary = self._compute_report_balance(summary)
                for key, value in res_summary.items():
                    for field in fields:
                        res[report.id][field] += value[field]

        return res
