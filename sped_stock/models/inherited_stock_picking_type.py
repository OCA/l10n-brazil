# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import models, fields


class SpedStockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        ondelete='cascade',
        domain=[('emissao', '=', '0'), ('modelo', 'in', ['55', '65', '59', '2D'])]
    )
