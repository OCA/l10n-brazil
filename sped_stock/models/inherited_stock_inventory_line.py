# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class InventoryLine(models.Model):
    _inherit = b'stock.inventory.line'

    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto',
        ondelete='restrict',
    )

    vr_unitario_custo = fields.Float(
        string='Valor Custo Unitário',
    )

    vr_total_custo = fields.Float(
        string='Valor Custo Total',
    )

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        """
        Sincronização do produto com product.product do core
        """
        for record in self:
            if record.produto_id:
                record.product_id = record.produto_id.product_id
