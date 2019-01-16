# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

MONTHS = {
    '01': 'Janeiro',
    '02': 'Fevereiro',
    '03': 'Março',
    '04': 'Abril',
    '05': 'Maio',
    '06': 'Junho',
    '07': 'Julho',
    '08': 'Agosto',
    '09': 'Setembro',
    '10': 'Outubro',
    '11': 'Novembro',
    '12': 'Dezembro',
}


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'

    administrator_id = fields.Many2one(
        string=u'Administrador responsável',
        comodel_name='res.partner',
        compute='_compute_responsible',
        readonly=False,
        store=True,
    )
    accountant_id = fields.Many2one(
        string=u'Contador responsável',
        comodel_name='res.partner',
        compute='_compute_responsible',
        readonly=False,
        store=True,
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
                'name': self.administrator_id.name or '',
                'label': 'Administrador - CPF: %s' %
                         (self.administrator_id.cnpj_cpf or '')},
            'accountant': {
                'signature': '______________________________________________',
                'name': self.accountant_id.name,
                'label': 'Contador - CPF: %s CRC: %s' % (
                    self.accountant_id.cnpj_cpf or '',
                    self.accountant_id.crc_number or '')},
        }]
        resolution = next(
            d['cols'][0]['val'] for d in res['content']
            if d['kpi_name'] == self.report_id.kpi_ids.filtered(
                lambda kpi: kpi.name == 'resultado_liquido_do_periodo'
            ).description)
        resolution = '{:,}'.format(float(resolution)).split('.')
        resolution = resolution[0].replace(',', '.') + ',' + resolution[1]
        res['resolution'] = resolution

        today = fields.Date.today()
        res['today'] = {
            'day': today[-2:],
            'month': MONTHS[today[5:-3]],
            'year': today[:4],
        }
        return res
