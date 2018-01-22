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

    def _sincroniza_sale_order(self):
        for picking in self:
            if not picking.group_id and not picking.origin:
                continue

            sale_order = None

            if picking.group_id:
                busca = [('procurement_group_id', '=', picking.group_id.id)]
                sale_order = self.env['sale.order'].search(busca)

            if not sale_order:
                busca = [('name', '=', picking.origin)]
                sale_order = self.env['sale.order'].search(busca)

            if sale_order:
                dados = {
                    'sale_order_id': sale_order.id,
                    'stock_picking_id': picking.id,
                    'note': sale_order.obs_estoque or '',
                }

                if sale_order.operacao_produto_id:
                    dados['operacao_id'] = sale_order.operacao_produto_id.id
                    sql = '''
                    update stock_picking set
                        sale_order_id = %(sale_order_id)s,
                        operacao_id = %(operacao_id)s,
                        note = %(note)s
                    where
                        id = %(stock_picking_id)s;
                    '''
                else:
                    sql = '''
                    update stock_picking set
                        sale_order_id = %(sale_order_id)s,
                        note = %(note)s
                    where
                        id = %(stock_picking_id)s;
                    '''

                self.env.cr.execute(sql, dados)

    @api.model
    def create(self, dados):
        picking = super(StockPicking, self).create(dados)
        picking._sincroniza_sale_order()
        return picking

    def write(self, dados):
        res = super(StockPicking, self).write(dados)
        self._sincroniza_sale_order()
        return res

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

        if not self.sale_order_id:
            return super(StockPicking, self).gera_documento()

        documento, nfse = \
            self.sale_order_id.gera_documento(
                    soh_produtos=True, stock_picking=self)

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

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        #
        # Reabre o pedido de venda
        #
        for picking in self:
            if not picking.sale_order_id:
                continue

            picking.sale_order_id.state = 'draft'
