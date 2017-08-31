# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class StockPicking(SpedCalculoImposto, models.Model):
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

    #
    # Limitamos as operações fiscais a emissão própria, e somente dos modelos
    # que movimentam produtos
    #
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        ondelete='cascade',
        domain=[('emissao', '=', '0'), ('modelo', 'in', ['55', '65', '59', '2D'])]
    )

    sped_documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='stock_picking_id',
        string='Documentos Fiscais',
        copy=False,
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        related='move_lines.produto_id',
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

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        self.ensure_one()

        if self.picking_type_id and self.picking_type_id.operacao_id:
            self.operacao_id = self.picking_type_id.operacao_id

    def prepara_dados_documento(self):
        self.ensure_one()

        return {
            'stock_picking_id': self.id,
        }

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(StockPicking, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(StockPicking, self).write(dados)
