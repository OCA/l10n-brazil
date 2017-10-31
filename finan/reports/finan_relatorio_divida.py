# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from collections import OrderedDict
from psycopg2.extensions import AsIs

from odoo import _
from odoo import fields, exceptions
from odoo.report import report_sxw
from ..constantes import *
from .report_xlsx_base import ReportXlsxBase

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import agora, formata_data

except (ImportError, IOError) as err:
    _logger.debug(err)


class FinanRelatorioDivida(ReportXlsxBase):
    def define_title(self):
        if self.report_wizard.group_by == 'data_vencimento_util':
            if self.report_wizard.tipo_divida == 'a_receber':
                title = 'Contas a Receber - por vencimento'
            else:
                title = 'Contas a Pagar - por vencimento'
        else:
            if self.report_wizard.tipo_divida == 'a_receber':
                title = 'Contas a Receber - por cliente'
            else:
                title = 'Contas a Pagar - por fornecedor'

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
            2: {
                'title': 'Situação',
                'value': FINAN_SITUACAO_DIVIDA_SIMPLES_DICT[
                        self.report_wizard.situacao_divida_simples],
            },

        }
        return filtros

    def define_filter_title_column_span(self):
        return 2

    def define_filter_value_column_span(self):
        return 3

    def _linhas_detalhe(self, report_data, filtros):
        SQL_ANALITICO = '''
        select
            fl.id,
            fc.codigo as conta_codigo,
            fc.nome as conta_nome,
            d.nome as documento,
            fl.numero,
            fl.data_documento,
            fl.data_vencimento_util,
            fl.data_pagamento,
            fl.vr_documento,
            fl.vr_quitado_juros,
            fl.vr_quitado_multa,
            fl.vr_quitado_desconto,
            fl.vr_quitado_total,
            fl.participante_id,
            coalesce(p.nome, '') as participante_nome,
            coalesce(p.cnpj_cpf, '') as participante_cnpj_cpf

        from
            finan_lancamento fl
            join finan_conta fc on fc.id = fl.conta_id
            join sped_participante p on p.id = fl.participante_id
            join finan_documento d on d.id = fl.documento_id

        where
            fl.provisorio != True
            and fl.tipo = %(tipo)s
            and fl.empresa_id = %(empresa_id)s
            and fl.data_vencimento_util between %(data_inicial)s and %(data_final)s
            and fl.situacao_divida_simples = %(situacao_divida_simples)s
        '''

        if self.report_wizard.participante_ids:
            SQL_ANALITICO += '''
            and fl.participante_id in %(participante_ids)s
            '''

        if self.report_wizard.group_by == 'data_vencimento_util':
            SQL_ANALITICO += '''
        order by
            fl.data_vencimento_util,
            coalesce(p.nome, ''),
            coalesce(p.cnpj_cpf, '')
            '''
        else:
            SQL_ANALITICO += '''
        order by
            coalesce(p.nome, ''),
            coalesce(p.cnpj_cpf, ''),
            fl.data_vencimento_util
            '''

        self.env.cr.execute(SQL_ANALITICO, filtros)
        dados = self.env.cr.dictfetchall()

        if not dados:
            raise exceptions.Warning(
                'Não foram encontrados dados com os filtros informados'
            )

        for linha in dados:
            participante = \
                self.env['sped.participante'].browse(linha['participante_id'])

            parceiro = participante.name_get()[0][1]
            if participante.email:
                parceiro += ' - ' + participante.email
            linha['parceiro'] = parceiro

            chave_grupo = linha[self.report_wizard.group_by]
            #
            # Acumula as linhas pelos grupos
            #
            if chave_grupo in report_data['linhas']:
                report_data['linhas'][chave_grupo].append(linha)
            else:
                report_data['linhas'][chave_grupo] = [linha]

    def _linhas_total_participante(self, report_data, filtros):
        SQL_RESUMO = '''
        select
            fl.participante_id,
            coalesce(p.nome, '') as participante_nome,
            coalesce(p.cnpj_cpf, '') as participante_cnpj_cpf,
            coalesce(sum(coalesce(fl.vr_documento, 0)), 0) as vr_documento,
            coalesce(sum(coalesce(fl.vr_quitado_juros, 0)), 0) as vr_quitado_juros,
            coalesce(sum(coalesce(fl.vr_quitado_multa, 0)), 0) as vr_quitado_multa,
            coalesce(sum(coalesce(fl.vr_quitado_desconto, 0)), 0) as vr_quitado_desconto,
            coalesce(sum(coalesce(fl.vr_quitado_total, 0)), 0) as vr_quitado_total

        from
            finan_lancamento fl
            join finan_conta fc on fc.id = fl.conta_id
            join sped_participante p on p.id = fl.participante_id

        where
            fl.provisorio != True
            and fl.tipo = %(tipo)s
            and fl.empresa_id = %(empresa_id)s
            and fl.data_vencimento_util between %(data_inicial)s and %(data_final)s
            and fl.situacao_divida_simples = %(situacao_divida_simples)s
        '''

        if self.report_wizard.participante_ids:
            SQL_RESUMO += '''
            and fl.participante_id in %(participante_ids)s
            '''

        SQL_RESUMO += '''
        group by
            fl.participante_id,
            coalesce(p.nome, ''),
            coalesce(p.cnpj_cpf, '')

        order by
            coalesce(p.nome, ''),
            coalesce(p.cnpj_cpf, '')
        '''

        self.env.cr.execute(SQL_RESUMO, filtros)
        dados = self.env.cr.dictfetchall()
        for linha in dados:
            participante = \
                self.env['sped.participante'].browse(
                    linha['participante_id'])

            parceiro = participante.name_get()[0][1]
            if participante.email:
                parceiro += ' - ' + participante.email
            linha['titulo_total'] = parceiro

            report_data['linhas_total'][linha['participante_id']] = linha

    def _linhas_total_data_vencimento_util(self, report_data, filtros):
        SQL_RESUMO = '''
        select
            fl.data_vencimento_util,
            coalesce(sum(coalesce(fl.vr_documento, 0)), 0) as vr_documento,
            coalesce(sum(coalesce(fl.vr_quitado_juros, 0)), 0) as vr_quitado_juros,
            coalesce(sum(coalesce(fl.vr_quitado_multa, 0)), 0) as vr_quitado_multa,
            coalesce(sum(coalesce(fl.vr_quitado_desconto, 0)), 0) as vr_quitado_desconto,
            coalesce(sum(coalesce(fl.vr_quitado_total, 0)), 0) as vr_quitado_total

        from
            finan_lancamento fl
            join finan_conta fc on fc.id = fl.conta_id
            join sped_participante p on p.id = fl.participante_id

        where
            fl.provisorio != True
            and fl.tipo = %(tipo)s
            and fl.empresa_id = %(empresa_id)s
            and fl.data_vencimento_util between %(data_inicial)s and %(data_final)s
            and fl.situacao_divida_simples = %(situacao_divida_simples)s
        '''

        if self.report_wizard.participante_ids:
            SQL_RESUMO += '''
            and fl.participante_id in %(participante_ids)s
            '''

        SQL_RESUMO += '''
        group by
            fl.data_vencimento_util

        order by
            fl.data_vencimento_util
        '''

        self.env.cr.execute(SQL_RESUMO, filtros)
        dados = self.env.cr.dictfetchall()
        for linha in dados:
            data_vencimento_util = \
                fields.Datetime.from_string(linha['data_vencimento_util'])
            data_vencimento_util = data_vencimento_util.strftime('%d/%m/%Y')

            linha['titulo_total'] = data_vencimento_util

            report_data['linhas_total'][linha['data_vencimento_util']] = linha

    def prepare_data(self):
        #
        # First, we prepare the report_data linhas, time_span and accounts
        #
        report_data = {
            'linhas': OrderedDict(),
            'linhas_total': OrderedDict(),
        }

        filtros = {
            'tipo': self.report_wizard.tipo_divida,
            'data_inicial': self.report_wizard.data_inicial,
            'data_final': self.report_wizard.data_final,
            'empresa_id': self.report_wizard.empresa_id.id,
            'situacao_divida_simples':
                self.report_wizard.situacao_divida_simples,
            'participante_ids':
                AsIs(tuple(self.report_wizard.participante_ids.ids)),
        }

        self._linhas_detalhe(report_data, filtros)

        #
        # Montamos agora os resumos por participande ou data
        #
        if self.report_wizard.group_by == 'participante_id':
            self._linhas_total_participante(report_data, filtros)

        elif self.report_wizard.group_by == 'data_vencimento_util':
            self._linhas_total_data_vencimento_util(report_data, filtros)

        return report_data

    def define_columns(self):
        result = {
            1: {
                'header': 'Documento',
                'field': 'documento',
                'width': 25,
            },
            2: {
                'header': 'Número',
                'field': 'numero',
                'width': 15,
            },
            3: {
                'header': 'Data',
                'field': 'data_documento',
                'width': 10,
                'style': 'date',
                'type': 'date',
            },
            4: {
                'header': 'Pagamento',
                'field': 'data_pagamento',
                'width': 15,
                'style': 'date',
                'type': 'date',

            },
            5: {
                'header': 'Valor',
                'field': 'vr_documento',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            6: {
                'header': 'Juros',
                'field': 'vr_quitado_juros',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            7: {
                'header': 'Multa',
                'field': 'vr_quitado_multa',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            8: {
                'header': 'Desconto',
                'field': 'vr_quitado_desconto',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            9: {
                'header': 'Pago',
                'field': 'vr_quitado_total',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
        }

        if self.report_wizard.group_by == 'data_vencimento_util':
            result[0] = {
                'header': 'Cliente' if \
                    self.report_wizard.tipo_divida == 'a_receber' \
                    else 'Fornecedor',
                'field': 'parceiro',
                'width': 60,
            }

        else:
            result[0] = {
                'header': 'Vencimento',
                'field': 'data_vencimento_util',
                'width': 15,
                'style': 'date',
                'type': 'date',
            }

        return result

    def define_columns_summary_total(self):
        result = {
            5: {
                'header': 'Valor',
                'field': 'vr_documento',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            6: {
                'header': 'Juros',
                'field': 'vr_quitado_juros',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            7: {
                'header': 'Multa',
                'field': 'vr_quitado_multa',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            8: {
                'header': 'Desconto',
                'field': 'vr_quitado_desconto',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
            9: {
                'header': 'Pago',
                'field': 'vr_quitado_total',
                'width': 15,
                'style': 'currency',
                'type': 'currency',
            },
        }

        if self.report_wizard.group_by == 'data_vencimento_util':
            result[0] = {
                'header': 'Cliente' if \
                    self.report_wizard.tipo_divida == 'a_receber' \
                    else 'Fornecedor',
                'field': 'titulo_total',
                'width': 60,
            }

        else:
            result[0] = {
                'header': 'Vencimento',
                'field': 'titulo_total',
                'width': 15,
                'style': 'date',
                'type': 'date',
            }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)

        titulos = {}

        self.write_header()

        for chave_grupo in self.report_data['linhas'].keys():
            if self.report_wizard.group_by == 'data_vencimento_util':
                data_vencimento_util = fields.Datetime.from_string(chave_grupo)
                data_vencimento_util = \
                    data_vencimento_util.strftime('%d/%m/%Y')
                titulos[chave_grupo] = 'Vencimento: ' + data_vencimento_util

                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    titulos[chave_grupo],
                    self.style.header.align_left
                )
                self.current_row += 1
                self.write_header()

            elif self.report_wizard.group_by == 'participante_id':
                participante = \
                    self.env['sped.participante'].browse(chave_grupo)

                parceiro = participante.name_get()[0][1]
                if participante.email:
                    parceiro += ' - ' + participante.email

                titulos[chave_grupo] = parceiro

                self.sheet.merge_range(
                    self.current_row, 0,
                    self.current_row + 1,
                    len(self.columns) - 1,
                    titulos[chave_grupo],
                    self.style.header.align_left
                )
                self.current_row += 2
                self.write_header()

            linha_atual = 0
            linhas_grupo = self.report_data['linhas'][chave_grupo]
            linha_total = self.report_data['linhas_total'][chave_grupo]
            for linha in linhas_grupo:
                #
                # Agora escreve a linha detalhe mesmo
                #
                self.write_detail(linha)
                linha_atual += 1

            #
            # Escreve o total de cada grupo
            #
            self.sheet.merge_range(
                self.current_row, 0,
                self.current_row + 1,
                len(self.columns) - 1,
                'Total',
                self.style.header.align_left
            )
            self.current_row += 1
            self.write_header()

            self.write_detail(linha_total)
            self.current_row += 1

        #
        # Agora, o total geral e o resumo
        #
        self.current_row += 1
        self.sheet.merge_range(
            self.current_row, 0,
            self.current_row + 1,
            len(self.columns) - 1,
            'Total Geral',
            self.style.header.align_left
        )
        self.current_row += 1
        self.write_header()


        total_columns = self.define_columns_summary_total()
        linha_total_geral = {
            'vr_documento': 0.00,
            'vr_quitado_juros': 0.00,
            'vr_quitado_multa': 0.00,
            'vr_quitado_desconto': 0.00,
            'vr_quitado_total': 0.00,
        }
        for chave_grupo in self.report_data['linhas_total']:
            linha_total = self.report_data['linhas_total'][chave_grupo]
            linha_total_geral['vr_documento'] += linha_total['vr_documento']
            linha_total_geral['vr_quitado_desconto'] += \
                linha_total['vr_quitado_desconto']
            linha_total_geral['vr_quitado_multa'] += \
                linha_total['vr_quitado_multa']
            linha_total_geral['vr_quitado_juros'] += \
                linha_total['vr_quitado_juros']
            linha_total_geral['vr_quitado_total'] += \
                linha_total['vr_quitado_total']

        first_data_row = self.current_row + 1
        self.write_detail(linha_total_geral, total_columns, first_data_row)

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(FinanRelatorioDivida, self).generate_xlsx_report(
            workbook, data, report_wizard)

        workbook.set_properties({
            'title': self.title.replace(' ', '_'),
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


FinanRelatorioDivida(
    #
    # Name of the report in report_xlsx_financial_cashflow_data.xml,
    # field name, *always* preceeded by 'report.'
    #
    'report.finan_relatorio_divida',
    #
    # The model used to filter report data, or where the data come from
    #
    'finan.relatorio.wizard',
    parser=report_sxw.rml_parse
)
