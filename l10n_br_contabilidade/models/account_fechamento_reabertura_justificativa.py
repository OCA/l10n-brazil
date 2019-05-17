# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountFechamentoReaberturaJustificativa(models.Model):
    _name = 'account.fechamento.reabertura.justificativa'

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
    fechamento_id = fields.Many2one(
        string='Fechamento',
        comodel_name='account.fechamento',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = 'Reabertura: {} - {}'.format(
                record.fechamento_id.name, record.data
            )
