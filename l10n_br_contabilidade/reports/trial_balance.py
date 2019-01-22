# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from operator import add
from openerp import tools

from openerp.addons.account_financial_report_webkit.report.trial_balance \
    import TrialBalanceWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser


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

    # in tests (when installing and testing at the same time),
    # the read below might fail because it relies on the order
    # given by parent_store
    if tools.config['test_enable']:
        account_obj._parent_store_compute(self.cursor)

    accounts = account_obj.read(
        self.cursor,
        self.uid,
        account_ids,
        ['type', 'code', 'name', 'debit', 'credit',
         'balance', 'parent_id', 'level', 'child_id'],
        context=ctx)

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
                if account.code == 'debito':
                    account['balance'] = account['init_balance'] + \
                                         account['debit'] - account['credit']
                else:
                    account['balance'] = account['init_balance'] + \
                                         account['credit'] - account['debit']
        accounts_by_id[account['id']] = account
    return accounts_by_id


def set_context(self, objects, data, ids, report_type=None):
    """Populate a ledger_lines attribute on each browse record that will
       be used by mako template"""
    objects, new_ids, context_report_values = self. \
        compute_balance_data(data)

    # Retira a conta 0 do relatório
    objects = objects.filtered(lambda x: x.code != '0')

    self.localcontext.update(context_report_values)

    return super(TrialBalanceWebkit, self).set_context(
        objects, data, new_ids, report_type=report_type)


TrialBalanceWebkit.set_context = set_context
TrialBalanceWebkit._get_account_details = _get_account_details

HeaderFooterTextWebKitParser(
    'report.account.abgf_account_report_trial_balance',
    'account.account',
    'abgf_contabilidade/reports/templates/account_report_trial_balance.mako',
    parser=TrialBalanceWebkit)
