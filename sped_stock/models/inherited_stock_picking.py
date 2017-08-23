# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)
from odoo.addons.l10n_br_base.constante_tributaria import (ENTRADA_SAIDA)


class SpedStockPicking(SpedCalculoImposto, models.Model):
    _inherit = 'stock.picking'

    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        related='sped_operacao_produto_id.entrada_saida'
    )

    @api.onchange('picking_type_id')
    def _onchange_stock_picking_type(self):
        for record in self:
            if record.picking_type_id:
                record.sped_operacao_produto_id = \
                    record.picking_type_id.operacao_id.id

    @api.multi
    def action_criar_sped_documento(self):
        for record in self:
            vals = record._prepare_sped(record.sped_operacao_produto_id)
            vals['item_ids'] = []
            for item in self.move_lines:
                vals['item_ids'].append((0, 0, item._prepare_sped_line()))
            documento = self.env['sped.documento'].create(vals)
            documento.item_ids.calcula_impostos()
            action = {
                'type': 'ir.actions.act_window',
                'name': 'Documento Gerado',  # TODO
                'res_model': 'sped.documento',  # TODO
                'domain': [('id', '=', documento.id)],  # TODO
                'view_mode': 'tree,form',
            }
            return action


class SpedStockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
    )
