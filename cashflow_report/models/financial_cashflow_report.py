# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinancialCashflowReport(models.Model):
    _name = b'cashflow_report.cashflow.report'
    _description = 'Financial Cashflow Report'

    name = fields.Char(
        string='Document Type',
        size=30,
        index=True,
    )

    data_maturity = fields.Char(
        string='Date Maturity',
    )

    data_payment = fields.Char(
        string='Date Maturity',
    )
