# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account_financial_report_webkit.report.print_journal \
    import PrintJournalWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser

import os


def set_context(self, objects, data, ids, report_type=None):
    """Populate a ledger_lines attribute on each browse record that will
       be used by mako template"""

    # Reading form
    main_filter = self._get_form_param('filter', data, default='filter_no')
    target_move = self._get_form_param('target_move', data, default='all')
    start_date = self._get_form_param('date_from', data)
    stop_date = self._get_form_param('date_to', data)
    start_period = self.get_start_period_br(data)
    stop_period = self.get_end_period_br(data)
    fiscalyear = self.get_fiscalyear_br(data)
    journal_ids = self._get_form_param('journal_ids', data)
    chart_account = self._get_chart_account_id_br(data)
    account_period_obj = self.pool.get('account.period')
    period_ids = account_period_obj.build_ctx_periods(self.cursor,
                                                      self.uid,
                                                      start_period.id,
                                                      stop_period.id)

    domain = [('journal_id', 'in', journal_ids)]
    if main_filter == 'filter_no':
        domain += [
            ('date', '>=',
             self.get_first_fiscalyear_period(fiscalyear).date_start),
            ('date', '<=',
             self.get_last_fiscalyear_period(fiscalyear).date_stop),
        ]
    # computation of move lines
    elif main_filter == 'filter_date':
        domain += [
            ('date', '>=', start_date),
            ('date', '<=', stop_date),
        ]
    elif main_filter == 'filter_period':
        domain = [
            ('period_id', 'in', period_ids),
        ]
    if target_move == 'posted':
        domain += [('state', '=', 'posted')]
    account_journal_period_obj = self.pool.get('account.journal.period')
    new_ids = account_journal_period_obj.search(self.cursor, self.uid, [
        ('journal_id', 'in', journal_ids),
        ('period_id', 'in', period_ids),
    ])
    objects = account_journal_period_obj.browse(self.cursor, self.uid,
                                                new_ids)
    # Sort by journal and period
    objects.sorted(key=lambda a: (a.journal_id.code,
                                  a.period_id.date_start))

    move_obj = self.pool.get('account.move')
    moves = {}
    account_journal_obj = self.pool.get('account.journal')
    journals = account_journal_obj.browse(self.cursor, self.uid, journal_ids)

    domain_arg = [
        ('period_id', 'in', period_ids),
    ]
    if target_move == 'posted':
        domain_arg += [('state', '=', 'posted')]
    move_ids = move_obj.search(self.cursor, self.uid, domain_arg,
                               order="date desc")
    moves = move_obj.browse(self.cursor, self.uid, move_ids)
    # Sort account move line by account accountant

    self.localcontext.update({
        'fiscalyear': fiscalyear,
        'start_date': start_date,
        'stop_date': stop_date,
        'start_period': start_period,
        'stop_period': stop_period,
        'chart_account': chart_account,
        'moves': moves,
    })

    return super(PrintJournalWebkit, self).set_context(
        journals, data, new_ids, report_type=report_type)


PrintJournalWebkit.set_context = set_context

HeaderFooterTextWebKitParser(
    'report.account.l10n_br_account_report_print_journal',
    'account.journal.period',
    os.path.dirname(os.path.abspath(__file__)) +
    '/templates/account_report_print_journal_webkit.mako',
    parser=PrintJournalWebkit)
