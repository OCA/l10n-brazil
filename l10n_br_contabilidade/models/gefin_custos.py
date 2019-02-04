# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class GefinCustos(models.Model):

    _name = 'gefin.custos'
    _description = 'Gefin Custos'
    _rec_name = 'period_id'
    _order = 'period_id'

    _sql_constraints = [
        ('period_uniq', 'unique(period_id)',
         'Período deve ser único'),
    ]

    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Periodo'
    )
    custo_fopag = fields.Float(
        string='FOPAG + Beneficios',
        digits=dp.get_precision('Account'),
    )
    custo_outros = fields.Float(
        string='Outros',
        digits=dp.get_precision('Account'),
    )
    date_start = fields.Date(
        related='period_id.date_start',
        store=True,
    )
    date_stop = fields.Date(
        related='period_id.date_stop',
        store=True,
    )
