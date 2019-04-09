# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import GeneralLedgerWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser


def get_account_reference(self, account_ids, account_depara_plano_id):
    """SELECT conta_sistema_id from account_mapeamento where
    account_depara_plano_id = 1 AND conta_referencia_id in (2294, 2298)"""

    sql_filters = {
        'conta_referencia_id': tuple(account_ids),
        'account_depara_plano_id': account_depara_plano_id,
    }

    sql_select = "SELECT conta_sistema_id FROM account_depara am"

    sql_where = "WHERE conta_referencia_id IN %(conta_referencia_id)s " \
                "AND account_depara_plano_id = %(account_depara_plano_id)s"

    sql_order = "order by conta_sistema_id"

    sql = ' '.join((sql_select, sql_where, sql_order))
    self.cursor.execute(sql, sql_filters)
    fetch_only_ids = self.cursor.fetchall()
    if not fetch_only_ids:
        return []
    only_ids = [only_id[0] for only_id in fetch_only_ids]
    return only_ids

def set_context(self, objects, data, ids, report_type=None):
    """Populate a ledger_lines attribute on each browse record that will be
    used by mako template"""
    lang = self.localcontext.get('lang')
    lang_ctx = lang and {'lang': lang} or {}
    new_ids = data['form']['account_ids'] or data[
        'form']['chart_account_id']
    situacao_lancamento = data['form'].get('target_move')

    # Account initial balance memoizer
    init_balance_memoizer = {}

    # Reading form
    main_filter = self._get_form_param('filter', data, default='filter_no')
    target_move = self._get_form_param('target_move', data, default='all')
    start_date = self._get_form_param('date_from', data)
    stop_date = self._get_form_param('date_to', data)
    do_centralize = self._get_form_param('centralize', data)
    start_period = self.get_start_period_br(data)
    stop_period = self.get_end_period_br(data)
    fiscalyear = self.get_fiscalyear_br(data)
    chart_account = self._get_chart_account_id_br(data)

    if main_filter == 'filter_no':
        start_period = self.get_first_fiscalyear_period(fiscalyear)
        stop_period = self.get_last_fiscalyear_period(fiscalyear)

    # computation of ledger lines
    if main_filter == 'filter_date':
        start = start_date
        stop = stop_date
    else:
        start = start_period
        stop = stop_period

    initial_balance = self.is_initial_balance_enabled(main_filter)
    initial_balance_mode = initial_balance \
                           and self._get_initial_balance_mode(start) or False

    # Retrieving accounts
    if data.get('form').get('account_depara_plano_id'):
        new_ids = get_account_reference(
            self, new_ids, data.get('form').get('account_depara_plano_id'))

    accounts = self.get_all_accounts(new_ids, exclude_type=['view'])
    if initial_balance_mode == 'initial_balance':
        init_balance_memoizer = self._compute_initial_balances(
            accounts, start, fiscalyear, situacao_lancamento=situacao_lancamento
        )
    elif initial_balance_mode == 'opening_balance':
        init_balance_memoizer = self._read_opening_balance(accounts, start)

    ledger_lines_memoizer = self._compute_account_ledger_lines(
        accounts, init_balance_memoizer, main_filter, target_move, start,
        stop)
    objects = self.pool.get('account.account').browse(self.cursor,
                                                      self.uid,
                                                      accounts,
                                                      context=lang_ctx)

    init_balance = {}
    ledger_lines = {}
    for account in objects:
        if do_centralize and account.centralized \
                and ledger_lines_memoizer.get(account.id):
            ledger_lines[account.id] = self._centralize_lines(
                main_filter, ledger_lines_memoizer.get(account.id, []))
        else:
            ledger_lines[account.id] = ledger_lines_memoizer.get(
                account.id, [])
        init_balance[account.id] = init_balance_memoizer.get(account.id,
                                                             {})

    self.localcontext.update({
        'fiscalyear': fiscalyear,
        'start_date': start_date,
        'stop_date': stop_date,
        'start_period': start_period,
        'stop_period': stop_period,
        'chart_account': chart_account,
        'initial_balance_mode': initial_balance_mode,
        'init_balance': init_balance,
        'ledger_lines': ledger_lines,
    })

    return super(GeneralLedgerWebkit, self).set_context(
        objects, data, new_ids, report_type=report_type)


GeneralLedgerWebkit.set_context = set_context

HeaderFooterTextWebKitParser(
    'report.account.l10n_br_account_report_general_ledger',
    'account.account',
    'l10n_br_contabilidade/reports/templates/account_report_general_ledger.mako',
    parser=GeneralLedgerWebkit)
