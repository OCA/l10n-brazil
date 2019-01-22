# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from openerp.addons.account_financial_report_webkit.report.trial_balance \
    import TrialBalanceWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser

HeaderFooterTextWebKitParser(
    'report.account.abgf_account_report_trial_balance',
    'account.account',
    os.path.dirname(os.path.abspath(__file__)) +
    '/templates/account_report_trial_balance.mako',
    parser=TrialBalanceWebkit)
