# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import GeneralLedgerWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser

HeaderFooterTextWebKitParser(
    'report.account.abgf_account_report_general_ledger',
    'account.account',
    'abgf_contabilidade/reports/templates/account_report_general_ledger.mako',
    parser=GeneralLedgerWebkit)
