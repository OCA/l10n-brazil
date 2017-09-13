# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _


class SpedProduto(models.Model):
    _inherit = 'sped.produto'

    estoque_em_maos = fields.Monetary(
        string='Estoque em mãos',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_disponivel = fields.Monetary(
        string='Estoque disponível',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_previsto_entrada = fields.Monetary(
        string='Estoque previsto (entradas)',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_comprometido_saida = fields.Monetary(
        string='Estoque comprometido (saídas)',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_minimo = fields.Monetary(
        string='Estoque mínimo',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_maximo = fields.Monetary(
        string='Estoque máximo',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )

    def _compute_estoque(self):
        for produto in self:
            produto.estoque_em_maos = produto.qty_available
            produto.estoque_disponivel = produto.virtual_available
            produto.estoque_previsto_entrada = produto.incoming_qty
            produto.estoque_comprometido_saida = produto.outgoing_qty
            produto.estoque_minimo = produto.reordering_min_qty
            produto.estoque_maximo = produto.reordering_max_qty
