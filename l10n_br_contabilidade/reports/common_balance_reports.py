# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from operator import add

from openerp.addons.account_financial_report_webkit.report.\
    common_balance_reports import CommonBalanceReportHeaderWebkit


def compute_balance_data(self, data, filter_report_type=None):
    new_ids = (data['form']['account_ids'] or
               [data['form']['chart_account_id']])
    max_comparison = self._get_form_param(
        'max_comparison', data, default=0)
    main_filter = self._get_form_param('filter', data, default='filter_no')

    comp_filters, nb_comparisons, comparison_mode = self._comp_filters(
        data, max_comparison)

    fiscalyear = self.get_fiscalyear_br(data)

    start_period = self.get_start_period_br(data)
    stop_period = self.get_end_period_br(data)

    target_move = self._get_form_param('target_move', data, default='all')
    start_date = self._get_form_param('date_from', data)
    stop_date = self._get_form_param('date_to', data)
    chart_account = self._get_chart_account_id_br(data)

    start_period, stop_period, start, stop = \
        self._get_start_stop_for_filter(main_filter, fiscalyear,
                                        start_date, stop_date,
                                        start_period, stop_period)

    init_balance = self.is_initial_balance_enabled(main_filter)
    initial_balance_mode = init_balance and self._get_initial_balance_mode(
        start) or False

    # Retrieving accounts
    ctx = {}
    if data['form'].get('account_level'):
        # Filter by account level
        ctx['account_level'] = int(data['form']['account_level'])
    account_ids = self.get_all_accounts(
        new_ids, only_type=filter_report_type, context=ctx)

    ctx['lancamento_de_fechamento'] = data['form']['lancamento_de_fechamento']
    # get details for each account, total of debit / credit / balance
    accounts_by_ids = self._get_account_details(
        account_ids, target_move, fiscalyear, main_filter, start, stop,
        initial_balance_mode, context=ctx)

    comparison_params = []
    comp_accounts_by_ids = []
    for index in range(max_comparison):
        if comp_filters[index] != 'filter_no':
            comparison_result, comp_params = self._get_comparison_details(
                data, account_ids, target_move, comp_filters[index], index)
            comparison_params.append(comp_params)
            comp_accounts_by_ids.append(comparison_result)

    objects = self.pool.get('account.account').browse(self.cursor,
                                                      self.uid,
                                                      account_ids)

    to_display_accounts = dict.fromkeys(account_ids, True)
    init_balance_accounts = dict.fromkeys(account_ids, False)
    comparisons_accounts = dict.fromkeys(account_ids, [])
    debit_accounts = dict.fromkeys(account_ids, False)
    credit_accounts = dict.fromkeys(account_ids, False)
    balance_accounts = dict.fromkeys(account_ids, False)

    for account in objects:
        if account.type == 'consolidation':
            to_display_accounts.update(
                dict([(a.id, False) for a in account.child_consol_ids]))
        elif account.type == 'view':
            to_display_accounts.update(
                dict([(a.id, True) for a in account.child_id]))
        debit_accounts[account.id] = \
            accounts_by_ids[account.id]['debit']
        credit_accounts[account.id] = \
            accounts_by_ids[account.id]['credit']
        balance_accounts[account.id] = \
            accounts_by_ids[account.id]['balance']
        init_balance_accounts[account.id] = \
            accounts_by_ids[account.id].get('init_balance', 0.0)

        # if any amount is != 0 in comparisons, we have to display the
        # whole account
        display_account = False
        comp_accounts = []
        for comp_account_by_id in comp_accounts_by_ids:
            values = comp_account_by_id.get(account.id)
            values.update(
                self._get_diff(account.balance, values['balance']))
            display_account = any((values.get('credit', 0.0),
                                   values.get('debit', 0.0),
                                   values.get('balance', 0.0),
                                   values.get('init_balance', 0.0)))
            comp_accounts.append(values)
        comparisons_accounts[account.id] = comp_accounts
        # we have to display the account if a comparison as an amount or
        # if we have an amount in the main column
        # we set it as a property to let the data in the report if someone
        # want to use it in a custom report
        display_account = display_account or any(
            (
                debit_accounts[account.id],
                credit_accounts[account.id],
                balance_accounts[account.id],
                init_balance_accounts[account.id]
            )
        )
        to_display_accounts.update(
            {account.id: display_account and to_display_accounts[account.id]}
        )

    context_report_values = {
        'fiscalyear': fiscalyear,
        'start_date': start_date,
        'stop_date': stop_date,
        'start_period': start_period,
        'stop_period': stop_period,
        'chart_account': chart_account,
        'comparison_mode': comparison_mode,
        'nb_comparison': nb_comparisons,
        'initial_balance': init_balance,
        'initial_balance_mode': initial_balance_mode,
        'comp_params': comparison_params,
        'to_display_accounts': to_display_accounts,
        'init_balance_accounts': init_balance_accounts,
        'comparisons_accounts': comparisons_accounts,
        'debit_accounts': debit_accounts,
        'credit_accounts': credit_accounts,
        'balance_accounts': balance_accounts,
    }

    return objects, new_ids, context_report_values


CommonBalanceReportHeaderWebkit.compute_balance_data = compute_balance_data
