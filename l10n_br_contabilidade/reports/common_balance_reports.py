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
        initial_balance_mode, context=ctx
    )

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
        debit_display = 0.0
        credit_display = 0.0
        balance_display = 0.0
        init_balance_display = 0.0
        if account.type == 'consolidation':
            to_display_accounts.update(
                dict([(a.id, False) for a in account.child_consol_ids]))
        elif account.type == 'view':
            to_display_accounts.update(
                dict([(a.id, True) for a in account.child_id]))
        debit_display = accounts_by_ids[account.id]['debit']
        credit_display = accounts_by_ids[account.id]['credit']
        balance_display = accounts_by_ids[account.id]['balance']
        init_balance_display = accounts_by_ids[account.id].get('init_balance', 0.0)

        debit_accounts[account.id] = debit_display
        credit_accounts[account.id] = credit_display
        balance_accounts[account.id] = balance_display
        init_balance_accounts[account.id] = init_balance_display

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
                init_balance_accounts[account.id])
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


def _get_account_details(self, account_ids, target_move, fiscalyear,
                         main_filter, start, stop, initial_balance_mode,
                         context=None):
    """
    Get details of accounts to display on the report
    @param account_ids: ids of accounts to get details
    @param target_move: selection filter for moves (all or posted)
    @param fiscalyear: browse of the fiscalyear
    @param main_filter: selection filter period / date or none
    @param start: start date or start period browse instance
    @param stop: stop date or stop period browse instance
    @param initial_balance_mode: False: no calculation,
           'opening_balance': from the opening period,
           'initial_balance': computed from previous year / periods
    @return: dict of list containing accounts details, keys are
             the account ids
    """
    if context is None:
        context = {}

    account_obj = self.pool.get('account.account')
    period_obj = self.pool.get('account.period')
    use_period_ids = main_filter in (
        'filter_no', 'filter_period', 'filter_opening')

    period_ids = False

    if use_period_ids:
        if main_filter == 'filter_opening':
            period_ids = [start.id]
        else:
            period_ids = period_obj.build_ctx_periods(
                self.cursor, self.uid, start.id, stop.id)
            # never include the opening in the debit / credit amounts
            period_ids = self.exclude_opening_periods(period_ids)

    init_balance = False
    if initial_balance_mode == 'opening_balance':
        init_balance = self._read_opening_balance(account_ids, start)
    elif initial_balance_mode:
        init_balance = self._compute_initial_balances(
            account_ids, start, fiscalyear)

    ctx = context.copy()
    ctx.update({'state': target_move,
                'all_fiscalyear': True})

    if use_period_ids:
        ctx.update({'periods': period_ids})
    elif main_filter == 'filter_date':
        ctx.update({'date_from': start,
                    'date_to': stop})

    accounts = account_obj.read(
        self.cursor,
        self.uid,
        account_ids,
        ['type', 'code', 'name', 'debit', 'credit',
            'balance', 'parent_id', 'level', 'child_id', 'type'],
        context=ctx)

    if 'lancamento_de_fechamento' in context and not \
            context['lancamento_de_fechamento']:
        accounts = _remove_close_moves(self, account_ids, accounts, period_ids)

    accounts_by_id = calc_parent_account_balance(
        self, account_obj, accounts, ctx, init_balance)
    return accounts_by_id


def calc_parent_account_balance(self, account_obj, accounts, ctx, init_balance):
    accounts_by_id = {}
    accounts_child = accounts
    accounts_dict_by_id = {}
    for acc in accounts_child:
        accounts_dict_by_id[acc['id']] = acc
    for account in accounts:
        if init_balance:
            # sum for top level views accounts
            child_ids = account_obj._get_children_and_consol(
                self.cursor, self.uid, account['id'], ctx)
            if account['child_id']:
                child_init_balances = [
                    init_bal['init_balance']
                    for acnt_id, init_bal in init_balance.iteritems()
                    if acnt_id in child_ids]
                top_init_balance = reduce(add, child_init_balances)
                account['init_balance'] = top_init_balance
                debit = 0.0
                credit = 0.0
                for child in accounts_child:
                    if child['id'] in child_ids and \
                            accounts_dict_by_id[child['id']][
                                'type'] == u'other':
                        debit += child['debit']
                        credit += child['credit']
                account['debit'] = debit
                account['credit'] = credit
            else:
                account['init_balance'] = init_balance[account['id']][
                    'init_balance']
            account['balance'] = account['init_balance'] + \
                                 account['debit'] - account['credit']
        accounts_by_id[account['id']] = account
    return accounts_by_id


def _remove_close_moves(self, account_ids, accounts, period_ids):
    close_moves = {}
    self.cursor.execute("SELECT account_id, debit, credit"
                        " FROM account_move_line l"
                        " JOIN account_move m on (l.move_id=m.id)"
                        " WHERE l.period_id in %s"
                        " AND l.account_id in %s"
                        " AND m.lancamento_de_fechamento = %s",
                        (tuple(period_ids), tuple(account_ids), True))
    for move_line in self.cursor.fetchall():
        close_moves[move_line[0]] = {
            'debit': move_line[1], 'credit': move_line[2]
        }

    for account in accounts:
        if account['type'] == 'other':
            if account['id'] in close_moves:
                if close_moves[account['id']]['debit']:
                    account['debit'] -= close_moves[account['id']]['debit']
                    account['balance'] -= close_moves[account['id']]['debit']
                else:
                    account['credit'] -= close_moves[account['id']]['credit']
                    account['balance'] += close_moves[account['id']]['credit']

    return accounts


CommonBalanceReportHeaderWebkit.compute_balance_data = compute_balance_data

CommonBalanceReportHeaderWebkit._get_account_details = _get_account_details
