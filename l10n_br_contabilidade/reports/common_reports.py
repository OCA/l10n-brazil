# -*- coding: utf-8 -*-
from operator import add

from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import CommonReportHeaderWebkit
from openerp.addons.account_financial_report_webkit.report.common_balance_reports import CommonBalanceReportHeaderWebkit


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
        display_account = display_account \
                          or any((debit_accounts[account.id],
                                  credit_accounts[account.id],
                                  balance_accounts[account.id],
                                  init_balance_accounts[account.id]))
        to_display_accounts.update(
            {account.id: display_account and
                         to_display_accounts[account.id]})

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

    accounts_by_id = {}
    for account in accounts:
        if init_balance:
            # sum for top level views accounts
            child_ids = account_obj._get_children_and_consol(
                self.cursor, self.uid, account['id'], ctx)
            if child_ids:
                child_init_balances = [
                    init_bal['init_balance']
                    for acnt_id, init_bal in init_balance.iteritems()
                    if acnt_id in child_ids]
                top_init_balance = reduce(add, child_init_balances)
                account['init_balance'] = top_init_balance
            else:
                account.update(init_balance[account['id']])
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


def _get_move_line_datas(self, move_line_ids,
                         order='per.special DESC, l.date ASC, \
                             per.date_start ASC, m.name ASC'):

    if not move_line_ids:
        return []
    if not isinstance(move_line_ids, list):
        move_line_ids = [move_line_ids]
    monster = """
SELECT l.id AS id,
            l.date AS ldate,
            j.code AS jcode ,
            j.type AS jtype,
            l.currency_id,
            l.account_id,
            l.amount_currency,
            l.ref AS lref,
            l.name AS lname,
            CASE
                WHEN LEFT(an.name, 1) = 'D' THEN
                    COALESCE(l.debit, 0.0) - COALESCE(l.credit, 0.0)
                ELSE
                    COALESCE(l.credit, 0.0) - COALESCE(l.debit, 0.0)
            END AS balance,
            l.debit,
            l.credit,
            l.period_id AS lperiod_id,
            per.code as period_code,
            per.special AS peropen,
            l.partner_id AS lpartner_id,
            p.name AS partner_name,
            m.name AS move_name,
            COALESCE(partialrec.name, fullrec.name, '') AS rec_name,
            COALESCE(partialrec.id, fullrec.id, NULL) AS rec_id,
            m.id AS move_id,
            c.name AS currency_code,
            i.id AS invoice_id,
            i.type AS invoice_type,
            i.number AS invoice_number,
            l.date_maturity,
            m.narration,
            m.sequencia,
            LEFT(an.name, 1) AS natureza
FROM account_move_line l
    JOIN account_move m on (l.move_id=m.id)
    INNER JOIN account_account aa on (l.account_id = aa.id)
    INNER JOIN account_natureza an on (aa.natureza_conta_id = an.id)
    LEFT JOIN res_currency c on (l.currency_id=c.id)
    LEFT JOIN account_move_reconcile partialrec
        on (l.reconcile_partial_id = partialrec.id)
    LEFT JOIN account_move_reconcile fullrec on (l.reconcile_id = fullrec.id)
    LEFT JOIN res_partner p on (l.partner_id=p.id)
    LEFT JOIN account_invoice i on (m.id =i.move_id)
    LEFT JOIN account_period per on (per.id=l.period_id)
    JOIN account_journal j on (l.journal_id=j.id)
    WHERE l.id in %s"""
    monster += (" ORDER BY %s" % (order,))
    try:
        self.cursor.execute(monster, (tuple(move_line_ids),))
        res = self.cursor.dictfetchall()
    except Exception:
        self.cursor.rollback()
        raise
    return res or []


def _compute_initial_balances(self, account_ids, start_period, fiscalyear):
    res = {}
    pnl_periods_ids = self._get_period_range_from_start_period(
        start_period, fiscalyear=fiscalyear, include_opening=True)
    bs_period_ids = self._get_period_range_from_start_period(
        start_period, include_opening=True, stop_at_previous_opening=True)
    opening_period_selected = self.get_included_opening_period(
        start_period)

    for acc in self.pool.get('account.account').browse(
            self.cursor, self.uid, account_ids):

        res[acc.id] = self._compute_init_balance(default_values=True)
        if acc.user_type.close_method == 'none':
            if pnl_periods_ids and not opening_period_selected:
                res[acc.id] = self._compute_init_balance(
                    acc.id, pnl_periods_ids)
        else:
            res[acc.id] = self._compute_init_balance(acc.id, bs_period_ids)

        # Aplicar o raciocinio da natureza da conta
        if acc.natureza_conta_id.code == 'credora':
            # quantidade de creditos maiores que debitos, o raciocinio inverte
            initial_balance = res.get(acc.id).get('init_balance') * -1
            res.get(acc.id).update(init_balance=initial_balance)

    return res


CommonReportHeaderWebkit._compute_initial_balances = _compute_initial_balances

CommonReportHeaderWebkit._get_move_line_datas = _get_move_line_datas

CommonBalanceReportHeaderWebkit.compute_balance_data = compute_balance_data

CommonBalanceReportHeaderWebkit._get_account_details = _get_account_details
