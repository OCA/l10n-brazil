# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountReaberturaPeriodoJustificativa(models.Model):
    _name = 'account.reabertura.periodo.justificativa'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee'
    )
    data = fields.Date(
        string='Data',
    )
    motivo = fields.Text(
        string='Justificativa'
    )
    period_id = fields.Many2one(
        string='Fechamento',
        comodel_name='account.period',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = 'Reabertura: {} - {}'.format(
                record.period_id.name, record.data
            )
