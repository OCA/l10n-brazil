# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class SpedStockPicking(SpedCalculoImposto, models.Model):
    _inherit = 'stock.picking'

    #
    # O campo item_ids serve para que a classe SpedCalculoImposto
    # saiba de quais itens virão os valores que serão somados nos
    # campos totalizados de impostos, valor do produto e valor da NF e fatura
    #
    item_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='picking_id',
        string='Itens de estoque',
    )
    sped_documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='stock_picking_id',
        string='Documentos Fiscais',
        copy=False,
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        related='order_line.produto_id',
        string='Produto',
        copy=False,
    )

    #
    # Datas sem hora no fuso horário de Brasília, para relatórios e pesquisas,
    # porque data sem hora é vida ;)
    #
    data = fields.Date(
        string='Data',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    data_conclusao = fields.Date(
        string='Data de conclusão',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    @api.depends('date', 'date_done')
    def _compute_data_hora_separadas(self):
        for picking in self:
            data, hora = self._separa_data_hora(picking.date)
            picking.data = data
            #picking.hora = hora

            data, hora = self._separa_data_hora(picking.date_done)
            picking.data_conclusao = data
            #picking.hora_conclusao = hora


    # documento_fiscal_criado = fields.Boolean(
    #     copy=False
    # )
    # documento_id = fields.Many2one(
    #     comodel_name='sped.documento',
    #     string='Documento Fiscal Relacionado'
    # )

    # @api.onchange('picking_type_id')
    # def _onchange_stock_picking_type(self):
    #     for record in self:
    #         if record.picking_type_id:
    #             record.operacao_id = \
    #                 record.picking_type_id.operacao_id.id
    #
    # def _criar_documento_itens(self, move_lines, documento):
    #     itens_ids = []
    #     for item in move_lines:
    #         doc_item = self.env['sped.documento.item'].create(
    #             item._prepare_sped_line(documento))
    #         # Mantemos relacionamento de ida e volta entre
    #         # documento_item e stock_move
    #         item.documento_item_id = doc_item
    #         itens_ids.append(doc_item.id)
    #     return itens_ids
    #
    # @api.multi
    # def action_criar_sped_documento(self):
    #     documentos_criados = []
    #     for record in self:
    #         vals = record._prepare_sped(record.operacao_id)
    #         documento = self.env['sped.documento'].create(vals)
    #
    #         itens_ids = self._criar_documento_itens(self.move_lines, documento)
    #         documento.item_ids = itens_ids
    #
    #         for item in documento.item_ids:
    #             item.calcula_impostos()
    #
    #         documentos_criados.append(documento.id)
    #         if documento.id:
    #             documento.stock_picking_id = record
    #             record.documento_fiscal_criado = True
    #             record.documento_id = documento
    #
    #     action = {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Documento Gerado',
    #         'res_model': 'sped.documento',
    #         'domain': [('id', 'in', documentos_criados)],
    #         'view_mode': 'tree,form',
    #     }
    #     return action

    def prepara_dados_sped_documento(self):
        self.ensure_one()

        return {
            'stock_picking_id': self.id,
        }
