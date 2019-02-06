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

    # Incluído a natureza da conta na busca
    accounts = account_obj.read(
        self.cursor,
        self.uid,
        account_ids,
        ['type', 'code', 'name', 'debit', 'credit',
         'balance', 'parent_id', 'level', 'child_id', 'natureza_conta_id'],
        context=ctx)

    accounts_by_id = {}
    for account in accounts:
        if init_balance:
            # sum for top level views accounts
            child_ids = account_obj._get_children_and_consol(
                self.cursor, self.uid, account['id'], ctx)
            if child_ids:

                child_init_balances = [
                    {'natureza_saldo_inicial': init_bal['natureza_conta'],
                     'balance': init_bal['init_balance']}
                    for acnt_id, init_bal in init_balance.iteritems()
                    if acnt_id in child_ids]

                filhas_devedoras = filter(
                    lambda x: x.get('natureza_saldo_inicial') == 'Devedora',
                    child_init_balances)
                total_debitos_filhas = \
                    sum(map(lambda x:x.get('balance'), filhas_devedoras))

                filhas_credoras = filter(
                    lambda x: x.get('natureza_saldo_inicial') == 'Credora',
                    child_init_balances)
                total_creditos_filhas = \
                    sum(map(lambda x:x.get('balance'), filhas_credoras))

                #
                # Saldo inicial tambem deve levar em consideração a
                # Natureza da conta

                # Se tiver natureza definida, conta de escrituracao
                if account.get('natureza_conta_id'):
                    if account.get('natureza_conta_id')[1] == 'Devedora':
                        top_init_balance = \
                            total_debitos_filhas - total_creditos_filhas
                    if account.get('natureza_conta_id')[1] == 'Credora':
                        top_init_balance = \
                            total_creditos_filhas - total_debitos_filhas

                # Conta analitica
                else:
                    top_init_balance = \
                        abs(total_debitos_filhas - total_creditos_filhas)

                account['init_balance'] = top_init_balance

                # Natureza do SALDO INICIAL
                # Se Conta credora e teve mais creditos, o saldo sera credor
                # Se Conta devedora e teve mais debitos, o saldo sera devedor
                # Se o 'balance' for negativo segnifica que a conta teve mais
                # lançamentos de natureza invertida.Logo a natureza deverá inverter
                if account.get('natureza_conta_id'):
                    if account.get('init_balance', 0.00) >= 0:
                        account['natureza_init_balance'] = \
                            account.get('natureza_conta_id')[1][:1]
                    else:
                        account['natureza_init_balance'] = 'D' \
                            if account.get('natureza_conta_id')[1][:1] == 'C' \
                            else 'C'
                else:
                    account['natureza_init_balance'] = 'D' \
                        if total_debitos_filhas > total_creditos_filhas else 'C'

            else:
                account.update(init_balance[account['id']])

            account['balance'] = account['init_balance'] + \
                                 account['debit'] - account['credit']

            # Se existir a natureza da conta
            if account.get('natureza_conta_id') and \
                    account.get('natureza_conta_id')[1] == 'Credora':
                account['balance'] = account['init_balance'] + \
                                     account['credit'] - account['debit']

            # Em contas analiticas, que nao tem natureza definida, levar em
            # consideracao a natureza do saldo inicial
            elif not account.get('natureza_conta_id') and \
                    account.get('natureza_init_balance') == 'C':
                account['balance'] = account['init_balance'] + \
                                     account['credit'] - account['debit']

            # Definir Natureza do SALDO FINAL
            if account.get('balance') > 0.0:
                natureza_balance = \
                    account.get('natureza_conta_id')[1][:1] \
                        if account.get('natureza_conta_id') \
                        else account.get('natureza_init_balance')

            if account.get('balance') < 0.0:
                if account.get('natureza_conta_id'):
                    natureza_balance = 'D' \
                        if account.get('natureza_conta_id')[1][:1] == 'C' \
                        else 'C'
                else:
                    natureza_balance = 'D' \
                        if account.get('natureza_init_balance') == 'C' \
                        else 'C'

            account['natureza_balance'] = \
                natureza_balance if account.get('balance') else ' '

        accounts_by_id[account['id']] = account
    return accounts_by_id


def compute_balance_data(self, data, filter_report_type=None):
    lang = self.localcontext.get('lang')
    lang_ctx = lang and {'lang': lang} or {}
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

    lang_ctx['lancamento_de_fechamento'] = \
        data['form']['lancamento_de_fechamento']

    # get details for each account, total of debit / credit / balance
    accounts_by_ids = self._get_account_details(
        account_ids, target_move, fiscalyear, main_filter, start, stop,
        initial_balance_mode, context=lang_ctx)

    comparison_params = []
    comp_accounts_by_ids = []
    for index in range(max_comparison):
        if comp_filters[index] != 'filter_no':
            comparison_result, comp_params = self._get_comparison_details(
                data, account_ids, target_move, comp_filters[index], index,
                context=lang_ctx)
            comparison_params.append(comp_params)
            comp_accounts_by_ids.append(comparison_result)

    objects = self.pool.get('account.account').browse(self.cursor,
                                                      self.uid,
                                                      account_ids,
                                                      context=lang_ctx)

    to_display_accounts = dict.fromkeys(account_ids, True)
    init_balance_accounts = dict.fromkeys(account_ids, False)
    natureza_init_balance_accounts = dict.fromkeys(account_ids, False)
    natureza_balance_accounts = dict.fromkeys(account_ids, False)
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
        natureza_init_balance_accounts[account.id] = \
            accounts_by_ids[account.id].get('natureza_init_balance', '')
        natureza_balance_accounts[account.id] = \
            accounts_by_ids[account.id].get('natureza_balance', '')

        # if any amount is != 0 in comparisons, we have to display the
        # whole account
        display_account = False
        comp_accounts = []
        for comp_account_by_id in comp_accounts_by_ids:
            values = comp_account_by_id.get(account.id)
            values.update(
                self._get_diff(balance_accounts[account.id],
                               values['balance']))
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
        'natureza_init_balance_accounts': natureza_init_balance_accounts,
        'natureza_balance_accounts': natureza_balance_accounts,
        'comparisons_accounts': comparisons_accounts,
        'debit_accounts': debit_accounts,
        'credit_accounts': credit_accounts,
        'balance_accounts': balance_accounts,
        'lancamentos_fechamento': data['form']['lancamento_de_fechamento'],
    }

    return objects, new_ids, context_report_values


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
TrialBalanceWebkit.compute_balance_data = compute_balance_data
TrialBalanceWebkit._get_account_details = _get_account_details

HeaderFooterTextWebKitParser(
    'report.account.l10n_br_account_report_trial_balance',
    'account.account',
    'l10n_br_contabilidade/reports/templates/account_report_trial_balance.mako',
    parser=TrialBalanceWebkit)
