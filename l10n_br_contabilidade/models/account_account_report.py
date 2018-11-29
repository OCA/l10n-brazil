# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models


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
    def get_total(self):
        """

        :return:
        """

        for record in self:

            if record.tipo_calculo == 'formula':
                pass


            elif record.tipo_calculo == 'conta':
                pass


        return 1234
