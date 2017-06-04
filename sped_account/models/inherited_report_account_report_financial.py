# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from .inherited_account_financial_report import (
    REPORT_TYPE, REPORT_TYPE_ACCOUNT_TYPE, REPORT_TYPE_ACCOUNTS,
    REPORT_TYPE_REPORT_VALUE, REPORT_TYPE_SUMMARY, REPORT_TYPE_VIEW,
)


class ReportAccountReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def get_account_lines(self, data):
        account_report = self.env['account.financial.report'].search(
            [('id', '=', data['account_report_id'][0])])

        if not account_report.is_brazilian_financial_report:
            return super(ReportAccountReportFinancial,
                         self)._get_account_lines(data)

        lines = []
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports, is_brazilian_financial_report=True)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports, is_brazilian_financial_report=True)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'],
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal']

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'],
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    def _compute_account_balance(self, accounts,
                                 is_brazilian_financial_report=True):
        if not is_brazilian_financial_report:
            return super(ReportAccountReportFinancial,
                         self)._compute_account_balance(accounts)

        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
            res[account.id]['redutora'] = account.redutora

        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + \
                      ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                if res[row['id']]['redutora']:
                    row['balance'] *= -1
                    row['debit'] *= -1
                    row['credit'] *= -1

                res[row['id']] = row

        return res


    def _compute_report_balance(self, reports,
                                is_brazilian_financial_report=True):
        if not is_brazilian_financial_report:
            return super(ReportAccountReportFinancial,
                         self)._compute_report_balance(reports)

        # import ipdb; ipdb.set_trace();

        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue

            res[report.id] = dict((fn, 0.0) for fn in fields)

            if report.type == REPORT_TYPE_ACCOUNTS:
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, is_brazilian_financial_report=True)

                #
                # Inverte o sinal de todos os valores em caso de item redutor
                #
                if report.redutor:
                    for account_id in res[report.id]['account']:
                        for field in fields:
                            res[report.id]['account'][field] *= -1

                #
                # Inverte o sinal *do saldo* quando necessário
                #
                if report.sign == -1:
                    for account_id in res[report.id]['account']:
                        res[report.id]['account'][account_id]['balance'] *= -1

                #
                # Acumula os valores das contas (já considerando caso redutor)
                #
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)

            elif report.type == REPORT_TYPE_ACCOUNT_TYPE:
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, is_brazilian_financial_report=True)

                #
                # Inverte o sinal de todos os valores em caso de item redutor
                #
                if report.redutor:
                    for account_id in res[report.id]['account']:
                        for field in fields:
                            res[report.id]['account'][account_id][field] *= -1

                #
                # Inverte o sinal *do saldo* quando necessário
                #
                if report.sign == -1:
                    for account_id in res[report.id]['account']:
                        res[report.id]['account'][account_id]['balance'] *= -1

                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)


            elif report.type == REPORT_TYPE_REPORT_VALUE and report.account_report_id:
                res2 = self._compute_report_balance(report.account_report_id, is_brazilian_financial_report=True)

                for key, value in res2.items():
                    for field in fields:
                        if report.redutor:
                            value[field] *= -1

                        if report.sign == -1 and field == 'balance':
                            value[field] *= -1

                        res[report.id][field] += value[field]

            elif report.type == REPORT_TYPE_VIEW:
                res2 = self._compute_report_balance(report.children_ids, is_brazilian_financial_report=True)

                for key, value in res2.items():
                    for field in fields:
                        if report.redutor:
                            value[field] *= -1

                        if report.sign == -1 and field == 'balance':
                            value[field] *= -1

                        res[report.id][field] += value[field]

            elif report.type == REPORT_TYPE_SUMMARY:
                for summary in report.summary_report_ids:
                    res_summary = self._compute_report_balance(summary, is_brazilian_financial_report=True)
                    for key, value in res_summary.items():
                        for field in fields:
                            if report.redutor:
                                value[field] *= -1

                            if report.sign == -1 and field == 'balance':
                                value[field] *= -1

                            res[report.id][field] += value[field]

        return res
