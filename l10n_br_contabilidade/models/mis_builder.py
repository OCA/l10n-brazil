# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'

    administrator_id = fields.Many2one(
        string=u'Administrador responsável',
        comodel_name='res.users',
        compute='_compute_responsible',
        readonly=False,
        store=False,
    )
    accountant_id = fields.Many2one(
        string=u'Contador responsável',
        comodel_name='res.users',
        compute='_compute_responsible',
        readonly=False,
        store=False,
    )

    @api.depends('date', 'company_id', 'period_ids')
    def _compute_responsible(self):
        for record in self:
            if not record.period_ids or (record.accountant_id and
                                         record.administrator_id):
                continue

            date_from = min(record.period_ids.mapped('date_from'))
            date_to = max(record.period_ids.mapped('date_to'))
            fiscal_years = self.env['account.fiscalyear'].search([
                '|',
                '&', ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                '&', ('date_stop', '>=', date_from),
                ('date_stop', '<=', date_to)
            ])
            accountants = fiscal_years.mapped('accountant_id')
            administrators = fiscal_years.mapped('administrator_id')
            if accountants:
                record.accountant_id = accountants[0]
            if administrators:
                record.administrator_id = administrators[0]

    @api.multi
    def compute(self):
        res = super(MisReportInstance, self).compute()
        res['footer'] = [{
            'administrator': {
                'signature': '______________________________________________',
                'label': 'Administrador responsável:',
                'name': self.administrator_id.name},
            'accountant': {
                'signature': '______________________________________________',
                'label': 'Contador responsável: ',
                'name': self.accountant_id.name},
        }]
        return res
