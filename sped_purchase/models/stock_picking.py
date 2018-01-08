# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_picking_type_code(self):
        for picking in self:
            picking.picking_type_code = picking.picking_type_id.code

    picking_type_code = fields.Char(
        compute='_compute_picking_type_code',
    )

    def action_view_purchase(self):

        action = self.env.ref('purchase.purchase_form_action').read()[0]

        if self.purchase_id:
            action['views'] = \
                [(self.env.ref('sped_purchase.purchase_order_form_view').id,
                  'form')]
            action['res_id'] = self.purchase_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action

    def gera_documento(self):
        if not self.purchase_id:
            return super(StockPicking, self).gera_documento()

        documento = self.purchase_id.gera_documento()

        if documento is None:
            return documento

        documento.stock_picking_id = self.id

        if self.modalidade_frete:
            documento.modalidade_frete = self.modalidade_frete

        if self.transportadora_id:
            documento.transportadora_id = self.transportadora_id.id

        if self.volume_ids:
            for volume in self.volume_ids:
                volume.documento_id = documento.id

        if documento.operacao_id.enviar_pelo_estoque:
            documento.envia_documento()

        return documento

    @api.onchange('state')
    def _onchange_state(self):
        self.ensure_one()
        if self.state == 'done' and self.purchase_id:
            self.purchase_id.state = 'received'
