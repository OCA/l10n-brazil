# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedStockSpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    stock_picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Operação de Estoque'
    )
