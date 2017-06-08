# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class TrialBalanceXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(TrialBalanceXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('CashFlow')

    def _get_report_columns(self, report):

        row_mes = 2

        result ={
            0: {'header': _('Conta'), 'field': '0', 'width': 12},

            1: {'header': _('Name'), 'field': '1', 'type': 'amount', 'width': 20},

        }

        for mes in self.env.context['fluxo_de_caixa']['meses']:
            result.update({
                row_mes: {'header': mes, 'field': row_mes, 'type': 'float', 'width': 10},
            })

            row_mes += 1

        return result

        # for col_pos, column in self.columns.iteritems():
        #     value = getattr(line_object, column['field'])
        #     cell_type = column.get('type', 'string')
        #     if cell_type == 'string':
        #         self.sheet.write_string(self.row_pos, col_pos, value or '')
        #     elif cell_type == 'amount':
        #         self.sheet.write_number(
        #             self.row_pos, col_pos, float(value), self.format_amount
        #         )
        # self.row_pos += 1

    def write_line(self, line_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.iteritems():

            value = line_object[int(column.get('field'))]

            if column.get('type') == 'float':
                self.sheet.write_number(self.row_pos, col_pos, value)
            else:
                self.sheet.write_string(self.row_pos, col_pos, value or '')

            # cell_type = column.get('type', 'string')
            # if column.get('field') == 'relacional':
            #     self.sheet.write_string(self.row_pos, col_pos, value or '')
            # else:
        self.row_pos += 1

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _generate_report_content(self, workbook, report):

        if not report.show_partner_details:
            # Display array header for account lines
            self.write_array_header()

        # For each account
        # for account in report.fluxo_de_caixa['']:
        for account in self.env.context['fluxo_de_caixa']['contas']:
            # Display account lines
            self.write_line(account)
        #
        #     else:
        #         # Write account title
        #         self.write_array_title(account.code + ' - ' + account.name)
        #
        #         # Display array header for partner lines
        #         self.write_array_header()
        #
        #         # For each partner
        #         for partner in account.partner_ids:
        #             # Display partner lines
        #             self.write_line(partner)
        #
        #         # Display account footer line
        #         self.write_account_footer(account,
        #                                   account.code + ' - ' + account.name)
        #
        #         # Line break
        #         self.row_pos += 2

    # def write_account_footer(self, account, name_value):
    #     """Specific function to write account footer for Trial Balance"""
    #     for col_pos, column in self.columns.iteritems():
    #         if column['field'] == 'name':
    #             value = name_value
    #         else:
    #             value = getattr(account, column['field'])
    #         cell_type = column.get('type', 'string')
    #         if cell_type == 'string':
    #             self.sheet.write_string(self.row_pos, col_pos, value or '',
    #                                     self.format_header_left)
    #         elif cell_type == 'amount':
    #             self.sheet.write_number(self.row_pos, col_pos, float(value),
    #                                     self.format_header_amount)
    #     self.row_pos += 1


TrialBalanceXslx(
    'report.cashflow_report.report_trial_balance_xlsx',
    'report_cashflow_qweb',
    parser=report_sxw.rml_parse
)
