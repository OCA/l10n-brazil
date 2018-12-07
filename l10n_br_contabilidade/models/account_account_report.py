# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models
from openerp.exceptions import Warning as UserError
from openerp.tools.safe_eval import safe_eval


class AccountAccountReport(models.Model):
    _name = b'account.account.report'
    _order = b'sequence'
    _description = 'Modelo para gerenciar contas nos relatórios.'

    active = fields.Boolean(
        string='Active?',
        default=True,
    )

    name = fields.Char(
        string='Nome',
    )

    code = fields.Char(
        string='Código',
        help='Código preferencialmente com letras maiúsculas '
             'separadas por underline _ '
    )

    mostrar_no_relatorio = fields.Boolean(
        string='Mostrar no relatório?',
        default=True,
        help='Algumas contas são de referência para contas totalizadoras não '
             'devendo aparecer nos relatórios',
    )

    type = fields.Selection(
        selection=[
            ('resultado','Demonstração de Resultado'),
            ('patrimonial','Patrimonial'),
        ],
        string='Tipo de Apresentação',
    )

    account_account_id = fields.Many2many(
        string=u'Contas',
        comodel_name='account.account',
        relation='account_account_account_report_rel',
        column1='account_account_id',
        column2='account_report_id',
    )

    sequence = fields.Integer(
        string='Sequência',
        help='Sequência de Apresentação das contas',
        unique=True,
    )

    sequence_execucao = fields.Integer(
        string='Sequência de execução',
        help='Sequência de Execução das contas.\n As contas de menor '
             'sequência serão processadas primeiro.',
        unique=True,
    )

    python_code = fields.Text(
        string='Fórmula',
        default='',
    )

    tipo_calculo = fields.Selection(
        string='Tipo de Cálculo',
        selection=[
            ('formula', 'Fórmula'),
            ('conta', 'Conta Analitica'),
            ('sintetico', 'Conta Sintético'),
        ],
        default='conta',
    )

    child_ids = fields.Many2many(
        comodel_name='account.account.report',
        string='Contas Para totalizar',
        relation='account_report_account_report_rel',
        column1='account_report_pai_id',
        column2='account_report_filha_id',
        domain="[('type', '=', type)]",
    )

    @api.multi
    @api.constrains('active')
    def _check_active(self):
        """
        :return:
        """
        for record in self:
            if not record.active:
                if record.child_ids:
                    raise UserError(
                        (u'Erro!'),
                        (u"Não é permitido desativar contas pertecentes a uma"
                         u" árvore. Certifique-se que essa conta não é pai de"
                         u" nenhuma outra e que não contenha contas filhas!"))

    @api.multi
    def get_total(self, partidas_ids=False, account_reports={}):
        """
        :return:
        """
        for record in self:

            if record.tipo_calculo == 'formula':

                safe_eval('result=' + record.python_code,
                          account_reports, mode='exec', nocopy=True)

                return account_reports.get('result', 0)

            elif record.tipo_calculo == 'conta':

                partidas_ids = self.env['account.move.line'].search([
                    ('id', 'in', partidas_ids._ids),
                    ('account_id', 'in', record.account_account_id._ids),
                ])

                total = \
                    sum(partidas_ids.mapped('debit')) - \
                    sum(partidas_ids.mapped('credit'))

                return total

            elif record.tipo_calculo == 'sintetico':
                account_report_ids = \
                    self.env['account.account.report.line'].search([
                        ('period_id', '=', record.period_id.id),
                        ('account_account_report_id','in',
                         record.child_ids._ids)
                    ])
                return sum(account_report_ids.mapped('total'))

    def gerar_reports(self, account_period_id, account_move_line_ids):
        """
        :param partidas:
        :return:
        """

        account_reports = {}

        account_account_reports_ids = self.search([
            ('active', '=', 'True'),
            ('type', '=', 'resultado'),
        ], order='sequence_execucao ASC')

        for account_account_reports_id in account_account_reports_ids:

            total = account_account_reports_id.get_total(
                account_move_line_ids, account_reports)

            if account_account_reports_id.mostrar_no_relatorio:
                # Criar linha baseado no template do account.report
                account_report_line = {
                    'name': account_account_reports_id.name,
                    'account_account_report_id': account_account_reports_id.id,
                    'period_id': account_period_id.id,
                    'total': total,
                }
                self.env['account.account.report.line'].create(
                    account_report_line)

            # Aproveitar o dicionario e complementar com informações das
            # linhas ja criadas para ser possivel utilizalas
            account_reports[account_account_reports_id.code] = total
