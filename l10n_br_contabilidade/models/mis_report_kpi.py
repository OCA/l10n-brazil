# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserWarning


EXPRESSION_TYPES = [
    ('bal', u'Saldo no período'),
    ('bale', u'Saldo no fim do período'),
    ('bali', u'Saldo no início do período'),
    ('crd', u'Credito no período'),
    ('crdi', u'Crédito no início do período'),
    ('crde', u'Crédito no fim do período'),
    ('deb', u'Débito no período'),
    ('debe', u'Débito no fim do período'),
    ('debi', u'Débito no início do período'),
]

SELECTION_MODE = [
    ('auto', u'Conta Contábil'),
    ('manual', u'Formula'),
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
    style_id = fields.Many2one(
        comodel_name='mis.report.style',
        string='Estilo',
    )
    account_ids = fields.Many2many(
        comodel_name='account.account',
        inverse_name='mis_report_kpi_ids',
        string='Contas contabeis'
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
        inverse='_inverse_kpi_expression',
        store=True,
        required=False,
    )
    expression_mode = fields.Selection(
        selection=SELECTION_MODE,
    )
    report_mode = fields.Char(
        # related='report_id.report_mode'
    )

    incluir_lancamentos_de_fechamento = fields.Boolean(
        string=u'Incluir lançamentos de fechamento?'
    )

    @api.one
    @api.onchange('report_mode')
    def onchange_report_mode(self):
        if self.report_mode == 'contabil':
            self.expression_mode = 'auto'
        else:
            self.expression_mode = 'manual'

    @api.one
    @api.constrains('account_ids')
    def _constrains_report_mode(self):
        if self.report_id.report_mode == 'contabil':
            if not self.account_ids and self.expression_mode == 'auto':
                raise UserWarning(
                    u"Não é possível criar um relatório contábil sem "
                    u"preencher as contas da linha"
                )

    @api.depends('account_ids.mis_report_kpi_ids', 'expression_type',
                 'invert_signal')
    def _compute_kpi_expression(self):
        for record in self:
            if record.expression_mode == 'manual':
                continue
            if not record.invert_signal and not record.expression_type and not\
                    record.account_ids:
                record.expression = ''
            else:
                signal = ''
                if record.invert_signal:
                    signal = '-'
                record.expression = (
                        signal +
                        record.expression_type +
                        '[{}]'.format(
                            "".join([str(acc.code) + ','
                                     if acc else ''
                                     for acc in record.account_ids])
                        )
                )

    @api.onchange('expression')
    def _onchange_kpi_expression(self):
        self._inverse_kpi_expression()

    def _test_exp_type(self, exp_t):
        return exp_t if (exp_t in [e[0] for e in EXPRESSION_TYPES]) else False

    def _inverse_kpi_expression(self):
        for record in self:
            if record.expression_mode == 'manual':
                continue

            exp = record.expression

            if not exp:
                continue
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
                raise UserWarning(u'Invalid expression type!')
