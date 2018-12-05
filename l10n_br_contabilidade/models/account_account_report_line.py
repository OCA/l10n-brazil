# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models


class AccountAccountReportLine(models.Model):
    _name = b'account.account.report.line'
    _order = b'sequence'
    _description = 'Modelo para gerenciar contas do Line.'

    name = fields.Char(
        string='Nome',
    )

    account_account_report_id = fields.Many2one(
        string=u'Conta Demonstrativa',
        comodel_name='account.account.report',
    )

    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Período',
    )

    total = fields.Float(
        string='Total Período'
    )

    sequence = fields.Integer(
        string='Sequência',
        help='Sequência de execução das contas',
        compute='compute_sequence',
        store=True,
    )

    @api.multi
    @api.depends('account_account_report_id')
    def compute_sequence(self):
        """
        :return:
        """
        for record in self:
            if record.account_account_report_id:
                record.sequence = record.account_account_report_id.sequence
