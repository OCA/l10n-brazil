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
        compute='_compute_vr_unitario_custo',
        store=True,
        inverse='_inverse_vr_unitario_custo',
    )

    def _inverse_vr_unitario_custo(self):
        """
        Função para possibilitar que o campo mesmo sendo computado, seja também
        editável. Esta função atualmente não faz nada, mas ficará como um hook 
        para futuras funcionalidades 
        """
        self.ensure_one()
        return True

    @api.depends('product_id')
    def _compute_vr_unitario_custo(self):
        """
        Função para calcular o preço de custo do produto que esta em estoque.
        TODO: Futuramente sera implementado o conceito de preço de custo médio
        do estoque.
        """
        for record in self:
            if record.product_id.price:
                record.vr_unitario_custo = record.product_id.price

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        """
        Sincronização do produto com product.product do core
        """
        for record in self:
            if record.produto_id:
                record.product_id = record.produto_id.product_id
