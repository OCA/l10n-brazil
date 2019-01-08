# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserWarning

EXPRESSION_TYPES = [
    ('bal', 'Saldo no período'),
    ('bale', 'Saldo no fim do período'),
    ('bali', 'Saldo no início do período'),
    ('crd', 'Credito no período'),
    ('crdi', 'Crédito no início do periodo'),
    ('crde', 'Crédito no fim do periodo'),
    ('deb', 'Débito no período'),
    ('debe', 'Débito no fim do período'),
    ('debi', 'Débito no início do período'),
]


class MisReportKpi(models.Model):

    _inherit = 'mis.report.kpi'

    @api.depends('style_id')
    def _compute_css_style(self):
        for record in self:
            record.default_css_style = record.style_id.to_css_style(
                record.style_id
            )

    default_css_style = fields.Char(
        compute='_compute_css_style',
        store=True,
    )
    account_ids = fields.Many2many(
        comodel_name='account.account',
        inverse_name='mis_report_kpi_ids'
    )
    invert_signal = fields.Boolean(
        default=False,
    )
    expression_type = fields.Selection(
        selection=EXPRESSION_TYPES,
        default='bal'
    )
    expression = fields.Char(
        compute='_compute_kpi_expression',
        inverse='_inverse_kpi_expression'
    )

    @api.depends('account_ids.mis_report_kpi_ids', 'expression_type',
                 'invert_signal')
    def _compute_kpi_expression(self):
        for record in self:
            if record.account_ids and record.expression_type:
                signal = ''
                if record.invert_signal:
                    signal = '-'
                record.expression = (
                        signal +
                        record.expression_type +
                        '[{}]'.format("".join([str(acc.code) + ',' if acc else ''
                                               for acc in record.account_ids])
                 ))
            else:
                record.expression = ''

    @api.onchange('expression')
    def _onchange_kpi_expression(self):
        self._inverse_kpi_expression()

    def _test_exp_type(self, exp_t):
        return exp_t if (exp_t in [e[0] for e in EXPRESSION_TYPES]) else False

    def _inverse_kpi_expression(self):
        for record in self:
            exp = record.expression

            if exp.startswith('-'):
                invert_signal = True
                exp_t = exp[1:].partition('[')[0]
            else:
                invert_signal = False
                exp_t = exp.partition('[')[0]

            if record._test_exp_type(exp_t):
                record.expression_type = record._test_exp_type(exp_t)

                record.invert_signal = invert_signal

                str_account_ids = exp.split('[', 1)[1].split(']')[0]
                account_ids = str_account_ids.split(',')
                record.account_ids = record.env['account.account'].search(
                    [('code', 'in', account_ids)])
            else:
                raise UserWarning('Invalid expression type!')
