# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class SpedStockDocumento(models.Model):
    _inherit = 'sped.documento'

    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Related Stock Picking',
        copy=False,
    )

    @api.multi
    def action_relacionar_picking(self):
        for record in self:
            if not record.stock_picking_id:
                related_picking = self.env['stock.picking'].search(
                    [('documento_id', '=', record.id)]
                )
                if related_picking:
                    record.stock_picking_id = related_picking
                else:
                    record._action_criar_picking()

    @api.multi
    def _action_criar_picking(self):
        for record in self:
            vals = {}
            vals = record._monta_dados_picking()
            picking = self.env['stock.picking'].create(vals)
            return picking

    def _get_valor(self, record, campo):
        valor = getattr(record, campo)
        if hasattr(valor, 'ids'):
            valor =  valor.ids

        return valor

    def _monta_dados_picking(self):
        vals = {}
        # Dados comuns ao stock_picking e o sped_documento
        for field in self._fields:
            if field in self.env['stock.picking']._fields and not field == 'id':
                valor = self._get_valor(self, field)
                vals.update({field: valor})

        # Dados específicos do stock_picking
        vals.update(self._get_campos_picking(self.operacao_id))

        # Dados do stock_move
        vals.update({'move_lines': []})
        for item in self.item_ids:
            move_line = {}
            for field in self.item_ids._fields:
                if field in self.env['stock.move']._fields and not \
                                field == 'id':
                    valor = self._get_valor(item, field)
                    move_line.update({field: valor})
            vals['move_lines'].append((0, 0, move_line))

        return vals

    def _get_campos_picking(self, operacao):
        customer_loc, supplier_loc = self.env[
            'stock.warehouse']._get_partner_locations()

        location_dest_id = customer_loc if \
            self.entrada_saida == '1' else supplier_loc

        location_src_id = customer_loc if \
            self.entrada_saida == '0' else supplier_loc

        return {
            'picking_type_id': operacao.stock_picking_type_id.id,
            'warehouse_id': operacao.stock_picking_type_id.warehouse_id.id,
            'location_id':
                operacao.stock_picking_type_id.default_location_src_id.id or
                location_src_id.id,
            'location_dest_id':
                operacao.stock_picking_type_id.default_location_dest_id.id or
                location_dest_id.id,
        }
