# -*- coding: utf-8 -*-
#
# Copyright 2017 Kmee Informática -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#
from odoo import api, fields, models, _


class SpedProdutoFornecedor(models.Model):
    _name = b'sped.produto.fornecedor'

    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto no estoque',
    )
