# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from ..constantes import *

REPORT_TYPE = [
    ('sum', 'View'),
    ('accounts', 'Accounts'),
    ('account_type', 'Account Type'),
    ('account_report', 'Report Value'),
    ('account_report_summary', 'Summarized Value'),
]
REPORT_TYPE_VIEW = 'sum'
REPORT_TYPE_ACCOUNTS = 'accounts'
REPORT_TYPE_ACCOUNT_TYPE = 'account_type'
REPORT_TYPE_REPORT_VALUE = 'account_report_value'
REPORT_TYPE_SUMMARY = 'account_report_summary'


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'
    # _parent_name = 'parent_id'
    # _parent_store = True
    # _parent_order = 'sequence, name'
    _order = 'parent_id, sequence'

    is_brazilian_financial_report = fields.Boolean(
        string='Is Brazilian Financial Report?',
    )
    summary_report_ids = fields.Many2many(
        comodel_name='account.financial.report',
        relation='account_financial_report_self',
        column1='report_id',
        column2='summary_report_id',
        string='Summarized Report',
    )
    type = fields.Selection(
        selection=REPORT_TYPE,
        string='Type',
        default=REPORT_TYPE_VIEW,
    )
