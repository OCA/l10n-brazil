# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class SpedTransmissao(models.Model):
    _inherit = 'sped.transmissao'

    employee_id = fields.Many2one(
        string='Funcionário',
        comodel_name='hr.employee',
        help='Guardar informações do Funcionario'
    )
