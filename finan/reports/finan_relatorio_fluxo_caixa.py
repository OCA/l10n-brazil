# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.exceptions import Warning
from odoo.report import report_sxw
from psycopg2.extensions import AsIs

from .report_xlsx_base import ReportXlsxBase

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import agora, formata_data

except (ImportError, IOError) as err:
    _logger.debug(err)


class FinanRelatorioFluxoCaixa(ReportXlsxBase):

    def define_title(self):
        if self.report_wizard.periodo == 'dias':
            if self.report_wizard.data_periodo == 'data_vencimento_util':
                title = 'Fluxo de Caixa - Diário - Previsto'
            else:
                title = 'Fluxo de Caixa - Diário - Realizado'

        elif self.report_wizard.periodo == 'semanas':
            if self.report_wizard.data_periodo == 'data_vencimento_util':
                title = 'Fluxo de Caixa - Semanal - Previsto'
            else:
                title = 'Fluxo de Caixa - Semanal - Realizado'

        else:
            if self.report_wizard.data_periodo == 'data_vencimento_util':
                title = 'Fluxo de Caixa - Mensal - Previsto'
            else:
                title = 'Fluxo de Caixa - Mensal - Realizado'

        return title

    def define_filters(self):
        data_inicial = \
            fields.Datetime.from_string(self.report_wizard.data_inicial)
        data_inicial = data_inicial.date()
        data_final = fields.Datetime.from_string(self.report_wizard.data_final)
        data_final = data_final.date()

        filtros = {
            0: {
                'title': 'Data',
                'value': 'De %s a %s' %
                (data_inicial.strftime('%d/%m/%Y'),
                 data_final.strftime('%d/%m/%Y')),
            },
            1: {
                'title': 'Empresa',
                'value': self.report_wizard.empresa_id.name_get()[0][1],
            },

        }

        print(filtros)
        return filtros

    def define_filter_title_column_span(self):
        return 2

    def define_filter_value_column_span(self):
        return 3

    def prepare_data(self):
        #
        # Primeiro, preparamos as linhas dos dados do relatório,
        # períodos e contas
        #
        report_data = {
            'titulo_data_periodo': {},
            'linhas': {},
            'resumos': {},
            'resumos_total': {},
            'resumos_acumulados': {},
        }

        data_inicial = fields.Datetime.from_string(self.report_wizard.data_inicial)
        data_inicial = data_inicial.date()
        data_final = fields.Datetime.from_string(self.report_wizard.data_final)
        data_final = data_final.date()

        if self.report_wizard.periodo == 'dias':
            data_atual = data_inicial
            while data_atual <= data_final:
                titulo = data_atual.strftime('%d/%m/%Y')
                data_periodo = 'valor_' + str(data_atual).replace('-', '_')
                report_data['titulo_data_periodo'][data_periodo] = titulo
                data_atual += relativedelta(dias=1)

        elif self.report_wizard.periodo == 'semanas':
            data_atual = data_inicial
            while data_atual <= data_final:
                titulo = data_atual.strftime('%V/%Y')
                data_periodo = 'valor_' + str(data_atual).replace('-', '_')
                report_data['titulo_data_periodo'][data_periodo] = titulo
                data_atual += relativedelta(semanas=1)
        else:
            data_atual = data_inicial + relativedelta(day=1)
            ultima_data = data_final + relativedelta(day=1)
            while data_atual <= ultima_data:
                titulo = data_atual.strftime('%B/%Y')
                data_periodo = 'valor_' + str(data_atual).replace('-', '_')
                report_data['titulo_data_periodo'][data_periodo] = titulo
                data_atual += relativedelta(months=1)

        contas = self.env['finan.conta'].search([], order='codigo')
        for conta in contas:
            linha = {
                'conta_codigo': conta.codigo,
                'conta_nome': conta.nome,
                'valor_inicial': 0,
                'valor_final': 0,
            }

            for data_periodo in report_data['titulo_data_periodo'].keys():
                linha[data_periodo] = 0

            report_data['linhas'][conta.codigo] = linha

            if conta.nivel == 1:
                report_data['resumos'][conta.codigo] = linha

        #
        # Agora as linhas dos resumos_total e resumos_acumulados
        #
        linha = {
            'conta_codigo': '',
            'conta_nome': 'TOTAL',
            'valor_inicial': 0,
            'valor_final': 0,
        }

        for data_periodo in report_data['titulo_data_periodo'].keys():
            linha[data_periodo] = 0

        report_data['resumos_total'] = linha

        linha = {
            'conta_codigo': '',
            'conta_nome': 'TOTAL GERAL',
            'valor_inicial': 0,
            'valor_final': 0,
        }

        for data_periodo in report_data['titulo_data_periodo'].keys():
            linha[data_periodo] = 0

        report_data['resumos_acumulados'] = linha

        #
        # Agora, os dados efetivos do relatório
        #
        filtro_sql = {
            'periodo': self.report_wizard.data_periodo,
            'data_inicial': self.report_wizard.data_inicial,
            'data_final': self.report_wizard.data_final,
            'empresa_id': int(self.report_wizard.empresa_id.id),
        }

        if self.report_wizard.data_periodo == 'data_vencimento_util':
            filtro_sql['tipo'] = 'in'

            if self.report_wizard.data_periodo == 'dias':
                filtro_sql['data_periodo'] = 'fl.data_vencimento_util'
            elif self.report_wizard.data_periodo == 'semanas':
                filtro_sql['data_periodo'] = \
                    "to_char(fl.data_vencimento_util, 'IYYY')"
            else:
                filtro_sql[
                    'data_periodo'] = \
                        "to_char(fl.data_vencimento_util, 'YYYY-MM-01')"

        else:
            filtro_sql['tipo'] = 'not in'

            if self.report_wizard.periodo == 'dias':
                filtro_sql['data_periodo'] = \
                    'coalesce(fl.data_credito_debito, fl.data_pagamento)'
            elif self.report_wizard.periodo == 'semanas':
                filtro_sql['data_periodo'] = \
                    "to_char(coalesce(fl.data_credito_debito, " + \
                    "fl.data_pagamento), 'IYYY')"
            else:
                filtro_sql['data_periodo'] = \
                    "to_char(coalesce(fl.data_credito_debito," + \
                    " fl.data_pagamento), 'YYYY-MM-01')"

        SQL_VALOR_INICIAL = '''
        select
            fc.codigo,
            coalesce(sum(coalesce(fl.vr_total, 0) * coalesce(fl.sinal, 1)), 0)
        from
            finan_lancamento fl
            join finan_conta_arvore fca on fca.conta_relacionada_id = fl.conta_id
            join finan_conta fc on fc.id = fca.conta_superior_id
        where
            fl.provisorio != True
            and fl.empresa_id = %(empresa_id)s
            and fl.tipo %(tipo)s ('a_receber', 'a_pagar')
            and fl.%(periodo)s < %(data_inicial)s

        group by
            fc.codigo

        order by
            fc.codigo
        '''

        filtros = {
            'tipo': AsIs(filtro_sql.get('tipo')),
            'periodo': AsIs(filtro_sql.get('periodo')),
            'data_inicial': filtro_sql.get('data_inicial'),
            'empresa_id': filtro_sql.get('empresa_id'),
        }
        self.env.cr.execute(SQL_VALOR_INICIAL, filtros)
        dados = self.env.cr.fetchall()

        if not dados:
            raise Warning(
                'Não foram encontrados dados com os filtros informados'
            )

        for conta_codigo, valor in dados:
            if conta_codigo in report_data['linhas']:
                report_data['linhas'][conta_codigo][
                    'valor_inicial'] = valor
                report_data['linhas'][conta_codigo]['valor_final'] = valor

            if conta_codigo in report_data['resumos']:
                report_data['resumos_total']['valor_inicial'] += valor
                report_data['resumos_total']['valor_final'] += valor

        SQL_DADOS = '''
        select
            fc.codigo,
            %(data_periodo)s as data_periodo,
            coalesce(sum(coalesce(fl.vr_total, 0) * coalesce(fl.sinal, 1)), 0)
        from
            finan_lancamento fl
            join finan_conta_arvore fca on fca.conta_relacionada_id = fl.conta_id
            join finan_conta fc on fc.id = fca.conta_superior_id
        where
            fl.provisorio != True
            and fl.empresa_id = %(empresa_id)s
            and fl.tipo %(tipo)s ('a_receber', 'a_pagar')
            and fl.%(periodo)s between %(data_inicial)s and %(data_final)s

        group by
            fc.id, fc.codigo, data_periodo

        order by
            fc.codigo, data_periodo
        '''

        filtros = {
            'data_periodo': AsIs(filtro_sql.get('data_periodo')),
            'tipo': AsIs(filtro_sql.get('tipo')),
            'periodo': AsIs(filtro_sql.get('periodo')),
            'data_inicial': filtro_sql.get('data_inicial'),
            'data_final': filtro_sql.get('data_final'),
            'empresa_id': filtro_sql.get('empresa_id'),
        }
        self.env.cr.execute(SQL_DADOS, filtros)
        dados = self.env.cr.fetchall()

        for conta_codigo, data_periodo, valor in dados:
            data_periodo = 'valor_' + data_periodo.replace('-', '_')
            if conta_codigo not in report_data['linhas']:
                # raise ?
                continue

            if data_periodo not in report_data['linhas'][conta_codigo]:
                # raise ?
                continue

            report_data['linhas'][conta_codigo][data_periodo] = valor
            report_data['linhas'][conta_codigo]['valor_final'] += valor

            if conta_codigo in report_data['resumos']:
                report_data['resumos_total'][data_periodo] += valor
                report_data['resumos_total']['valor_final'] += valor

        return report_data

    def define_columns(self):
        result = {
            0: {
                'header': 'Conta',
                'field': 'conta_codigo',
                'width': 12,
            },
            1: {
                'header': 'Conta',
                'field': 'conta_nome',
                'width': 25,
            },
            2: {
                'header': 'Inicial',
                'field': 'valor_inicial',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
        }

        titulo_data_periodo = self.report_data['titulo_data_periodo']

        next_col = 3
        for data_periodo in sorted(titulo_data_periodo.keys()):
            result[next_col] = {
                'header': titulo_data_periodo[data_periodo],
                'field': data_periodo,
                'style': 'currency',
                'width': 20,
                'type': 'currency',
            }
            next_col += 1

        result[next_col] = {
            'header': 'Final',
            'field': 'valor_final',
            'style': 'currency',
            'width': 20,
            'type': 'formula',
            'formula':
                '=SUM(C{current_row}:{previous_column}{current_row})',
        }

        return result

    def define_columns_summary_total(self):
        result = {
            0: {
                'header': 'Conta',
                'field': 'conta_codigo',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': 'Conta',
                'field': 'conta_nome',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': 'Inicial',
                'field': 'valor_inicial',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '=SUM({current_column}{first_row}:'
                    '{current_column}{previous_row})',
            },
        }

        titulo_data_periodo = self.report_data['titulo_data_periodo']

        next_col = 3
        for data_periodo in sorted(titulo_data_periodo.keys()):
            result[next_col] = {
                'header': titulo_data_periodo[data_periodo],
                'field': data_periodo,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '=SUM({current_column}{first_row}:'
                '{current_column}{previous_row})',
            }
            next_col += 1

        result[next_col] = {
            'header': 'Final',
            'field': 'valor_final',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '=SUM(C{current_row}:{previous_column}{current_row})',
        }

        return result

    def define_columns_summary_accumulated(self):
        result = {
            0: {
                'header': 'Conta',
                'field': 'conta_codigo',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': 'Conta',
                'field': 'conta_nome',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': 'Inicial',
                'field': 'valor_inicial',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{previous_row}',
            },
        }

        titulo_data_periodo = self.report_data['titulo_data_periodo']

        next_col = 3
        for data_periodo in sorted(titulo_data_periodo.keys()):
            result[next_col] = {
                'header': titulo_data_periodo[data_periodo],
                'field': data_periodo,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={previous_column}{current_row} + '
                '{current_column}{previous_row}',
            }
            next_col += 1

        result[next_col] = {
            'header': 'Final',
            'field': 'valor_final',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={previous_column}{current_row}',
        }

        return result

    def define_columns_detail_total(self):
        result = {
            0: {
                'header': 'Conta',
                'field': 'conta_codigo',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': 'Conta',
                'field': 'conta_nome',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': 'Inicial',
                'field': 'valor_inicial',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{linha_resumo_total}',
            },
        }

        titulo_data_periodo = self.report_data['titulo_data_periodo']

        next_col = 3
        for data_periodo in sorted(titulo_data_periodo.keys()):
            result[next_col] = {
                'header': titulo_data_periodo[data_periodo],
                'field': data_periodo,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={current_column}{linha_resumo_total}',
            }
            next_col += 1

        result[next_col] = {
            'header': 'Final',
            'field': 'valor_final',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={current_column}{linha_resumo_total}',
        }

        return result

    def define_columns_detail_accumulated(self):
        result = {
            0: {
                'header': 'Conta',
                'field': 'conta_codigo',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': 'Conta',
                'field': 'conta_nome',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': 'Inicial',
                'field': 'valor_inicial',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{linha_resumo_acumulado}',
            },
        }

        titulo_data_periodo = self.report_data['titulo_data_periodo']

        next_col = 3
        for data_periodo in sorted(titulo_data_periodo.keys()):
            result[next_col] = {
                'header': titulo_data_periodo[data_periodo],
                'field': data_periodo,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={current_column}{linha_resumo_acumulado}',
            }
            next_col += 1

        result[next_col] = {
            'header': 'Final',
            'field': 'valor_final',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={current_column}{linha_resumo_acumulado}',
        }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)

        self.write_header()
        #
        # Resumo
        #
        colunas_totais = self.define_columns_summary_total()
        colunas_acumuladas = self.define_columns_summary_accumulated()

        self.sheet.merge_range(
            self.current_row, 0, self.current_row + 1, len(self.columns) - 1,
            'CONTAS SINTÉTICAS', self.style.header.align_center
        )
        self.current_row += 2
        #self.write_header()

        primeira_linha_dados = self.current_row + 1
        for conta_codigo in sorted(self.report_data['resumos'].keys()):
            self.write_detail(self.report_data['resumos'][conta_codigo])

        self.write_detail(self.report_data['resumos_total'], colunas_totais,
                          primeira_linha_dados)
        linha_resumo_total = self.current_row
        self.write_detail(self.report_data['resumos_acumulados'],
                          colunas_acumuladas)
        linha_resumo_acumulado = self.current_row

        #
        # Detalhe
        #
        colunas_totais = self.define_columns_detail_total()
        colunas_acumuladas = self.define_columns_detail_accumulated()
        formula_changes = {
            'linha_resumo_total': linha_resumo_total,
            'linha_resumo_acumulado': linha_resumo_acumulado,
        }

        self.current_row += 1
        self.sheet.merge_range(
            self.current_row, 0, self.current_row + 1, len(self.columns) - 1,
            'CONTAS ANALÍTICAS', self.style.header.align_center
        )
        self.current_row += 2
        #self.write_header()

        primeira_linha_dados = self.current_row
        for conta_codigo in sorted(self.report_data['linhas'].keys()):
            self.write_detail(self.report_data['linhas'][conta_codigo])

        self.write_detail(self.report_data['resumos_total'], colunas_totais,
                          primeira_linha_dados, formula_changes=formula_changes)
        self.write_detail(self.report_data['resumos_acumulados'],
                          colunas_acumuladas, formula_changes=formula_changes)

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(FinanRelatorioFluxoCaixa, self).generate_xlsx_report(
            workbook, data, report_wizard)

        workbook.set_properties({
            'filename': 'Fluxo_de_Caixa.xlsx',
            'title': self.title,
            'company': self.report_wizard.empresa_id.name_get()[0][1],
            'comments': 'Criado pelo módulo financeiro dia {agora}'.format(
                agora=formata_data(agora(), '%d/%m/%Y às %H:%M:%S'))
        })

        #
        # Documentação para a formação das páginas aqui:
        # http://xlsxwriter.readthedocs.io/page_setup.html
        #
        self.sheet.set_landscape()
        self.sheet.set_paper(9)  # A4
        self.sheet.fit_to_pages(1, 99999)
        #
        # Margens, em polegadas, esquerda, direita, superior, inferior;
        # 1 / 2.54 = 1 cm convertido em polegadas
        #
        self.sheet.set_margins(1 / 2.54, 1 / 2.54, 1 / 2.54, 1 / 2.54)


FinanRelatorioFluxoCaixa(
    #
    # Nome do relatório, no campo "name",
    # no arquivo report_xlsx_finan_fluxo_caixa_data.xml,
    # *SEMPRE* precedido por "report."
    #
    'report.finan_relatorio_fluxo_caixa',
    #
    # O model usado para filtrar os dados do relatório, ou de onde vão vir os
    # dados
    #
    'finan.relatorio.wizard',
    parser=report_sxw.rml_parse
)
