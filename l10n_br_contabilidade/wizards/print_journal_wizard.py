# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from datetime import datetime, timedelta
import pandas as pd
import base64
import xlsxwriter


class AccountReportGeneralLedgerWizard(models.TransientModel):
    _inherit = 'print.journal.webkit'

    account_depara_plano_id = fields.Many2one(
        string='Referência Plano de Contas',
        comodel_name='account.depara.plano',
    )

    exibe_criador_aprovador = fields.Boolean(
        string='Exibir criador e aprovador')

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

        # Pega os as partidas dos movimentos.
        line_ids = self.env['account.move'].search([
            ('journal_id', 'in', data['datas']['form']['journal_ids']),
            ('period_id.name', 'in', periods),
            ('fiscalyear_id', '=', data['datas']['form']['fiscalyear_id']),
            ('state', '=', 'posted')]).mapped('line_id')

        # Cria a dict para receber as informações da busca.
        diario = {u'Data': [], u'Sequência do Lançamento': [], u'Conta': [],
                  u'Diário': [], u'Criado por': [], u'Validado por': [],
                  u'Histórico': [], u'Débito': [], u'Crédito': []} \
            if data['datas']['form']['exibe_criador_aprovador'] \
            else {u'Data': [], u'Sequência do Lançamento': [], u'Conta': [],
                  u'Diário': [], u'Histórico': [], u'Débito': [],
                  u'Crédito': []}

        for line in line_ids:
            diario[u'Data'].append(line.move_id.date or None)
            diario[u'Sequência do Lançamento'].append(line.move_id.sequencia
                                                     or None)
            diario[u'Conta'].append(line.account_id.code or None)
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
        columns = [u'Data', u'Sequência do Lançamento', u'Conta', u'Diário',
                   u'Criado por', u'Validado por', u'Histórico', u'Débito',
                   u'Crédito'] \
            if data['datas']['form']['exibe_criador_aprovador'] else \
            [u'Data', u'Sequência do Lançamento', u'Conta', u'Diário',
             u'Histórico', u'Débito', u'Crédito']

        # Cria o Dataframe e define a ordem das colunas.
        df = pd.DataFrame.from_dict(diario)
        df = df.reindex(columns=columns)

        # Cria o arquivo e passa o dataframe para o excel
        filename = 'diario_xls.xlsx'
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=4)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Formato do header
        header_format = workbook.add_format(
            {'bold': True,
             'text_wrap': True,
             'valign': 'top',
             'fg_color': '#D7E4BC',
             'border': 1})

        ano_fiscal = self.env['account.fiscalyear'].browse(
            data['datas']['form']['fiscalyear_id']).name

        worksheet.write(0, 0, 'Ano Fiscal', header_format)
        worksheet.write(1, 0, ano_fiscal, header_format)

        worksheet.write(0, 1, 'Filtro de Períodos', header_format)
        worksheet.write(1, 1, 'De: {} até {}'.format(periods[0], periods[-1]),
                        header_format)

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
