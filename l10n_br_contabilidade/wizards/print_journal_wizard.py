# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from datetime import datetime, timedelta
import pandas as pd
import base64
import os


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'print.journal.webkit'

    account_depara_plano_id = fields.Many2one(
        string='Referência Plano de Contas',
        comodel_name='account.depara.plano',
    )

    exibe_criador_aprovador = fields.Boolean(
        string='Exibir criador e aprovador')

    exibe_diario_origem = fields.Boolean(
        string='Exibir diário de origem',
        default=True,
    )

    diario_xls = fields.Binary(string='Diario')

    @api.multi
    def range_periodo(self, period_from, period_to):
        '''
        Pega os periodos dentro dos parametros definidos

        :param period_from:
        :param period_to:
        :return:
        '''
        period_from = self.env['account.period'].browse(period_from)
        period_to = self.env['account.period'].browse(period_to)

        ctr_from = datetime.strptime(period_from.date_start, '%Y-%m-%d')
        ctr_to = datetime.strptime(period_to.date_start, '%Y-%m-%d')
        period_range = [ctr_from.strftime('%m/%Y')]

        while ctr_from <= ctr_to:
            ctr_from += timedelta(days=32)
            period_range.append(
                datetime(ctr_from.year, ctr_from.month, 1).strftime('%m/%Y'))

        return period_range

    def letra_numero(self, num):
        abc = []
        for k in range(ord('A'), ord('Z') + 1):
            abc.append(chr(k))

        return abc[num]

    @api.multi
    def xls_report(self):
        '''
        Gera o relatório em XLS.
        :return:
        '''

        # Pega as informações dos métodos já existentes.
        data = self.check_report()
        data = self._print_report(data['datas'])

        # Periodos dentro do range definido.
        periods = self.range_periodo(
            period_from=data['datas']['form']['period_from'],
            period_to=data['datas']['form']['period_to'])

        depara_id = data.get('datas').get('form').\
            get('account_depara_plano_id')

        # Pega os as partidas dos movimentos.
        line_ids = self.env['account.move'].search([
            ('journal_id', 'in', data['datas']['form']['journal_ids']),
            ('period_id.name', 'in', periods),
            ('fiscalyear_id', '=', data['datas']['form']['fiscalyear_id']),
            ('state', '=', 'posted')]).mapped('line_id')

        # Cria a dict para receber as informações da busca.
        diario = {u'Data': [], u'Sequência do Lançamento': [], u'Conta': [],
                  u'Histórico': [], u'Débito': [], u'Crédito': []}

        if data['datas']['form']['exibe_diario_origem']:
            diario.update({u'Diário': []})

        # Adiciona quem criou e aprovou o lançamento.
        if data['datas']['form']['exibe_criador_aprovador']:
            diario.update({u'Criado por': [], u'Validado por': []})

        for line in line_ids:
            if depara_id:
                depara_account_id = False
                for depara_line in line.account_id.depara_ids:
                    if depara_line.account_depara_plano_id.id == depara_id:
                        depara_account_id = depara_line.conta_referencia_id
                        break
            if depara_id:
                account_id = depara_account_id
            else:
                account_id = line.account_id
            if not depara_id or depara_id and account_id:
                diario[u'Data'].append(line.move_id.date or None)
                diario[u'Sequência do Lançamento'].append(
                    line.move_id.sequencia or None)
                diario[u'Conta'].append(account_id.code or None)
                if data['datas']['form']['exibe_diario_origem']:
                    diario[u'Diário'].append(line.journal_id.name or None)
                diario[u'Histórico'].append(line.name or None)
                diario[u'Débito'].append(line.debit or 0)
                diario[u'Crédito'].append(line.credit or 0)
                if data['datas']['form']['exibe_criador_aprovador']:
                    diario[u'Criado por'].append(
                        line.move_id.criado_por.name or None)
                    diario[u'Validado por'].append(
                        line.move_id.validado_por.name or None)

        # Colunas do dataframe.
        columns = [u'Data', u'Sequência do Lançamento', u'Conta', u'Histórico',
                   u'Débito', u'Crédito']
        if data['datas']['form']['exibe_diario_origem']:
            columns.insert(columns.index(u'Conta')+1, u'Diário')
        if data['datas']['form']['exibe_criador_aprovador']:
            columns.insert(columns.index(u'Diário')+1
                           if u'Diário' in columns
                           else columns.index(u'Conta')+1, u'Validado Por')
            columns.insert(columns.index(u'Validado Por')+1, u'Criado por')

        # Cria o Dataframe e define a ordem das colunas.
        df = pd.DataFrame.from_dict(diario)
        df = df.reindex(columns=columns)

        # Converte e formata a coluna para o tipo data
        df['Data'] = pd.to_datetime(df['Data'])
        df['Data'] = df['Data'].dt.strftime('%d-%m-%Y')

        # Cria o arquivo e passa o dataframe para o excel
        filename = 'diario_xls.xlsx'
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=9)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Formato para quebra de linha quando texto não couber na célula
        wrap_format = workbook.add_format({'text_wrap': True, 'font_size': 9,
                                           'font_name': 'Arial'})

        # Tamanho das celulas de acordo com o tamanho do texto
        for col in columns:
            max_cell = df[col].map(str).map(len).max() + 1
            max_len = len(col) if len(col) > max_cell else max_cell
            cell = self.letra_numero(columns.index(col))
            max_len = max_len if max_cell < 60 else 60
            worksheet.set_column('{}:{}'.format(cell, cell), max_len,
                                 wrap_format)

        topo_format = workbook.add_format({'fg_color': '#1F295A'})

        # Formato do header
        header_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFFFF', 'font_name': 'Arial'})
        header_format.set_align('center')
        header_format.set_font_size(20)

        # Formato dos parametros
        parametros_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter', 'font_color': '#FFFFFF',
            'fg_color': '#1F295A', 'font_name': 'Arial'})
        parametros_format.set_align('center')

        ano_fiscal = self.env['account.fiscalyear'].browse(
            data['datas']['form']['fiscalyear_id']).name

        ultima_coluna = self.letra_numero(int(round(len(columns) - 1)))

        # TOPO
        worksheet.merge_range('A1:{}2'.format(ultima_coluna),
                              '', topo_format)
        # Header
        worksheet.merge_range('A3:{}7'.format(ultima_coluna),
                              'Relatórios - Livro Diário', header_format)

        # Ajustes de acordo com o número de colunas
        fim_coluna_1 = self.letra_numero(int(round((len(columns)-1)/2)))
        inicio_coluna_2 = self.letra_numero(int((round(len(columns)-1)/2))+1)

        # Parametros
        worksheet.merge_range('A8:{}8'.format(fim_coluna_1),
                              'Ano Fiscal: {}'.format(ano_fiscal),
                              parametros_format)

        worksheet.merge_range('{}8:{}8'.format(inicio_coluna_2, ultima_coluna),
                              'Períodos: De: {} até {}'.format(periods[0],
                                                               periods[-1]),
                              parametros_format)

        # Logo na celula B2
        img = os.path.dirname(os.path.realpath(__file__)
                              ).replace('/wizards', '/data/img/logo.png')
        worksheet.insert_image('B4', img, {'x_scale': 2, 'y_scale': 2})

        # 9 primeiras colunas fixadas.
        worksheet.freeze_panes(10, 0)

        writer.save()

        # Salva o arquivo gerado
        for record in self:
            record.diario_xls = base64.b64encode(
                open(filename, "rb").read())

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/print_journal_xls?&id=%s' % (record.id),
                'target': 'self',
            }

    @api.multi
    def _print_report(self, data):
        data['form']['exibe_criador_aprovador'] = self.exibe_criador_aprovador
        data['form']['exibe_diario_origem'] = self.exibe_diario_origem
        data['form']['account_depara_plano_id'] = \
            self.account_depara_plano_id.id
        data = self.pre_print_report(data)
        data = \
            super(AccountReportGeneralLedgerWizard, self)._print_report(data)

        if self.env.context.get('xls_export'):
            return data

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.l10n_br_account_report_print_journal',
                'datas': data}
