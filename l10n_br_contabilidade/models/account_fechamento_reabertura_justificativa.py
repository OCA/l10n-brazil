# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning


class AccountFechamentoReaberturaJustificativa(models.Model):
    _name = 'account.fechamento.reabertura.justificativa'

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
