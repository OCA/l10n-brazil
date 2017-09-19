# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto_produto_servico \
    import SpedCalculoImpostoProdutoServico
from odoo.addons.l10n_br_base.constante_tributaria import *


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido de Venda',
    )

    def _sincroniza_sale_order(self, dados):
        for picking in self:
            if not picking.group_id:
                continue

            busca = [('procurement_group_id', '=', picking.group_id.id)]
            sale_order = self.env['sale.order'].search(busca)

            if sale_order:
                dados['sale_order_id'] = sale_order.id

                if sale_order.operacao_produto_id:
                    dados['operacao_id'] = sale_order.operacao_produto_id.id

        return dados

    @api.model
    def create(self, dados):
        dados = self._sincroniza_sale_order(dados)
        return super(StockPicking, self).create(dados)

    def write(self, dados):
        dados = self._sincroniza_sale_order(dados)
        return super(StockPicking, self).write(dados)

    def action_view_sale(self):
        action = \
            self.env.ref('sped_sale.sale_order_orcamento_action').read()[0]

        if self.sale_order_id:
            action['views'] = [
                (self.env.ref('sped_sale.sale_order_form').id, 'form')]
            action['res_id'] = self.sale_order_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def gera_documento(self):
        self.ensure_one()

        if self.sale_order_id:
            documento, nfse = \
                self.sale_order_id.gera_documento(soh_produtos=True)
            documento.stock_picking_id = self.id

            if documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA:
                documento._confirma_estoque()
            elif documento.situacao_nfe in \
                (SITUACAO_NFE_CANCELADA, SITUACAO_NFE_DENEGADA):
                documento._cancela_estoque()

        else:
            documento = super(StockPicking, self).gera_documento()

        return documento
