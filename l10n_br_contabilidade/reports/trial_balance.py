# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account_financial_report_webkit.report.trial_balance \
    import TrialBalanceWebkit

from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix \
    import HeaderFooterTextWebKitParser


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

HeaderFooterTextWebKitParser(
    'report.account.abgf_account_report_trial_balance',
    'account.account',
    'abgf_contabilidade/reports/templates/account_report_trial_balance.mako',
    parser=TrialBalanceWebkit)
