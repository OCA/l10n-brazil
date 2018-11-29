# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models
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
    )

    account_account_id = fields.Many2many(
        string=u'Contas',
        comodel_name='account.account',
    )

    identificacao_saldo = fields.Selection(
        string='Natureza de Conta',
        selection=[
            ('debito', 'D'),
            ('credito', 'C'),
        ],
    )

    sequence = fields.Integer(
        string='Sequência',
        help='Sequência de execução das contas',
        unique=True,
    )

    python_code = fields.Text(
        string='Fórmula',
        default='',

    )

    tipo_calculo = fields.Selection(
        string='Tipo de Cálculo',
        selection=[
            ('conta', 'Contas'),
            ('formula', 'Fórmula'),
        ],
        default='conta',
    )

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
