# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sped_produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto',
        ondelete='cascade',
    )

    @api.model
    def create(self, vals):

        # Setar o campo obrigatorio do core
        if 'nome' in vals:
            vals.update(name=vals.get('nome'))

        # Criar o product.product
        product_id = super(ProductProduct, self).create(vals)

        # Se a criacao do produto nao vier do sped.produto,
        # criar o sped.produto referente
        if "create_from_sped_produto" not in self._context:
            product_id.create_sped_produto()
        return product_id

    @api.multi
    def create_sped_produto(self):
        sped_produto_obj = self.env["sped.produto"]
        for product_id in self:
            new_sped_produto = sped_produto_obj.create({
                'product_id': product_id.id,
            })
        return True
