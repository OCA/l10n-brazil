# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    carteira_id = fields.Many2one(
        string='Carteira Padrão',
        comodel_name='finan.carteira',
        help='Carteira para geração do boleto',
    )
