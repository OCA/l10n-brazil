# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase


class ChangeProductQuantity(SpedBase, models.TransientModel):
    _inherit = 'stock.change.product.qty'

    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto',
        ondelete='restrict',
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
        ondelete='restrict',
    )
    currency_unidade_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade',
        related='unidade_id.currency_id',
        readonly=True,
    )
    quantidade = fields.Monetary(
        string='Nova quantidade em mãos',
        default=1,
        currency_field='currency_unidade_id',
    )

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        self.ensure_one()

        self.product_id = self.produto_id.product_id.id
        self.unidade_id = self.produto_id.unidade_id

    @api.onchange('quantidade')
    def _onchange_quantidade(self):
        self.ensure_one()
        self.new_quantity = self.quantidade

    @api.model
    def default_get(self, fields):
        res = super(ChangeProductQuantity, self).default_get(fields)

        if self.env.context.get('active_id') and \
            self.env.context.get('active_model') == 'sped.produto':
            produto = self.env['sped.produto'].browse(
                self.env.context['active_id'])

            res['produto_id'] = produto.id
            res['product_id'] = produto.product_id.id
            res['product_tmpl_id'] = produto.product_id.product_tmpl_id.id
            res['unidade_id'] = produto.unidade_id.id

        return res
