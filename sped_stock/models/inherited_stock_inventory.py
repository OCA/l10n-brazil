# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase


class StockInventory(SpedBase, models.Model):
    _inherit = 'stock.inventory'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        ondelete='restrict',
        default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.empresa')
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Dono dos produtos',
        ondelete='restrict',
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto',
        ondelete='restrict',
    )

    def _sincroniza_empresa_company_participante_partner(self):
        for inventario in self:
            inventario.company_id = inventario.empresa_id.company_id

            if inventario.participante_id:
                inventario.partner_id = inventario.participante_id.partner_id

            if inventario.produto_id:
                inventario.product_id = inventario.produto_id.product_id

    @api.onchange('empresa_id', 'participante_id', 'produto_id')
    def _onchange_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.depends('empresa_id', 'participante_id', 'produto_id')
    def _depends_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.model
    def _selection_filter(self):
        res_filter = [
            ('none', 'Todos os produtos'),
            #('category', _('One product category')),
            ('product', 'Somente 1 produto'),
            ('partial', 'Escolher produtos manualmente')
        ]

        #if self.user_has_groups('stock.group_tracking_owner'):
            #res_filter += [('owner', _('One owner only')), ('product_owner', _('One product for a specific owner'))]
        #if self.user_has_groups('stock.group_production_lot'):
            #res_filter.append(('lot', _('One Lot/Serial Number')))
        #if self.user_has_groups('stock.group_tracking_lot'):
            #res_filter.append(('pack', _('A Pack')))

        return res_filter

    def _get_inventory_lines_values(self):
        """
        Sobrescrita da função do core que retorna as quantidades de produtos
        para o inventário. Nessa sobrescrita adicionamos trazemos a informação 
        do sped_produto_id em cada linha do inventário.         
        """
        product_obj = self.env['product.product']
        lines = super(StockInventory, self)._get_inventory_lines_values()
        for line in lines:
            product_id = product_obj.browse(line.get('product_id'))
            line['produto_id'] = product_id.sped_produto_id.id
        return lines
