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
            0: {'header': _('Conta'), 'field': 'code', 'width': 12},
            1: {'header': _('Name'), 'field': 'name', 'width': 25},
        }

        meses = self.env.context['fluxo_de_caixa']['meses']
        for mes in sorted(meses):
            result.update({
                row_mes: {
                    'header': meses[mes].values()[0],
                    'field': 'dados',
                    'type': 'float',
                    'width': 15,
                    'mes_ano': meses[mes].keys()[0],
                },
            })
            row_mes += 1
        return result

    def _get_report_columns_resumo(self, report):

        row_mes = 2

        result = {
            0: {'header': _('Conta'), 'field': '0', 'width': 12},
            1: {'header': _('Resumo'), 'field': '1', 'type': 'amount',
                'width': 25},
        }

        for mes in self.env.context['fluxo_de_caixa']['meses']:
            result.update({
                row_mes: {'header': mes, 'field': row_mes, 'type': 'float',
                          'width': 15},
            })

            row_mes += 1

        return result

    def write_line(self, line_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.iteritems():

            # Pega o nome do field, e busca na linha pelo field
            value = line_object.get(column.get('field'))

            # Se for do tipo valor, deverá corresponder com mes-ano
            if column.get('type') == 'float':
                # Valor padrao para o float
                valor = 0.00
                # Para cada dado na linha com chave == mes-valor
                for mes_ano in value.iterkeys():

                    if column.get('mes_ano') == mes_ano:
                        valor = value[mes_ano]

                self.sheet.write_number(self.row_pos, col_pos, valor, self.format_amount)

            # Se nao for float é string
            else:
                self.sheet.write_string(self.row_pos, col_pos, value or '')

        self.row_pos += 1

    def write_line_resumo(self, line_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns_resumo.iteritems():
            value = line_object[int(column.get('field'))]
            if column.get('type') == 'float':
                self.sheet.write_number(self.row_pos, col_pos, value)
            else:
                self.sheet.write_string(self.row_pos, col_pos, value or '')
        self.row_pos += 1

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def write_linha_soma(self):
        alfabeto = '.ABCDEFGHIJKLMNOPQRSTUVWYXZ'
        qtd_linhas = len(self.env.context['fluxo_de_caixa']['resumo'])
        for col_pos, column in self.columns.iteritems():
            if column.get('type') == 'float':
                celula = alfabeto[col_pos+1] + str(self.row_pos+1)
                formula = '{=SUM(%s%s:%s%s)}' % (
                    alfabeto[col_pos+1], str(self.row_pos-qtd_linhas),
                    alfabeto[col_pos+1], str(self.row_pos),
                )
                self.sheet.write_formula(celula, formula, self.format_amount)
            else:
                if col_pos == 1:
                    self.sheet.write_string(
                        self.row_pos, col_pos, 'SALDO' or '')
        self.row_pos += 1

    def write_linha_soma_acumulativa(self):
        alfabeto = '.ABCDEFGHIJKLMNOPQRSTUVWYXZ'
        primeira = True # Primeira celula da linha tem a formula diferenciada
        for col_pos, column in self.columns.iteritems():
            if column.get('type') == 'float':
                celula = alfabeto[col_pos+1] + str(self.row_pos+1)
                formula = '{=%s%s+%s%s}' % (
                    alfabeto[col_pos], str(self.row_pos+1),
                    alfabeto[col_pos+1], str(self.row_pos),
                )
                if primeira:
                    formula = '{=%s%s}' % (
                        alfabeto[col_pos+1], str(self.row_pos)
                    )
                    primeira = False
                self.sheet.write_formula(celula, formula, self.format_amount)
            else:
                if col_pos == 1:
                    self.sheet.write_string(
                        self.row_pos, col_pos, 'SALDO ACUMULATIVO' or '')
        self.row_pos += 1

    def _generate_report_content(self, workbook, report):

        # Set zoom
        self.sheet.set_zoom(85)

        # Display array header for account lines
        self.write_array_header()

        # For each account
        for account in self.env.context['fluxo_de_caixa']['contas']:
            # Display account lines
            self.write_line(self.env.context['fluxo_de_caixa']['contas'][account])

        # Cabeçalho do resumo
        self.write_array_header()

        for resumo in self.env.context['fluxo_de_caixa']['resumo']:
            # Display resume
            self.write_line(self.env.context['fluxo_de_caixa']['contas'][resumo])

        # Cria um alinha com formulas de SOMA e nome das contas na coluna de conta
        self.write_linha_soma()

        # Cria um alinha com formulas de SOMA ACUMULANDO os valores do periodo anterior
        self.write_linha_soma_acumulativa()

        # self.write_line_resumo(['','Saldo Final'] + self.env.context['fluxo_de_caixa']['saldo_final'])
        # self.write_line_resumo(['','Saldo Acumulado'] + self.env.context['fluxo_de_caixa']['saldo_acumulado'])
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
    'report.cashflow_report.report_financial_cashflow_xlsx',
    'report_financial_cashflow',
    parser=report_sxw.rml_parse
)
