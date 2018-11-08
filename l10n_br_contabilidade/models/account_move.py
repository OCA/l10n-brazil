# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    natureza_conta_id = fields.Many2one(
        string='Natureza da Conta',
        comodel_name='account.natureza',
    )

    centro_custo_id = fields.Many2one(
        string='Centro de Custo',
        comodel_name='account.centro.custo',
    )
