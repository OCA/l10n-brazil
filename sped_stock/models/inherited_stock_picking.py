# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)
from odoo.addons.l10n_br_base.constante_tributaria import (
    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO,
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
    documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='stock_picking_id',
        string='Documentos Fiscais',
        copy=False,
    )
    quantidade_documentos = fields.Integer(
        string='Quantidade de documentos fiscais',
        compute='_compute_quantidade_documentos_fiscais',
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

    move_type = fields.Selection(
        default='one',
    )

    #
    # Volumes da NF-e
    #
    volume_ids = fields.One2many(
        comodel_name='sped.documento.volume',
        inverse_name='stock_picking_id',
        string='Volumes'
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

    @api.depends('documento_ids.situacao_fiscal')
    def _compute_quantidade_documentos_fiscais(self):
        for picking in self:
            documento_ids = picking.documento_ids.search(
                [('stock_picking_id', '=', picking.id), ('situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            picking.quantidade_documentos = len(documento_ids)

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

    def gera_documento(self):
        self.ensure_one()

        documento = super(StockPicking, self).gera_documento()

        if documento is None:
            return documento

        if self.volume_ids:
            for volume in self.volume_ids:
                volume.documento_id = documento.id

        if documento.operacao_id.enviar_pelo_estoque:
            documento.envia_documento()

        return documento

    def unlink(self):
        #
        # Não permitimos excluir picking concluído ou cancelado
        #
        for picking in self:
            if picking.state == 'done':
                raise UserError(
                    'Você não pode excluir movimentações de estoque '
                    'concluídas!')
            elif picking.state == 'cancel':
                raise UserError(
                    'Você não pode excluir movimentações de estoque '
                    'canceladas!')

        return super(StockPicking, self).unlink()

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()

        for picking in self:
            if not picking.group_id:
                continue

            #
            # Apaga os procurement.order vinculados ao picking, pois isso
            # está causando sérios problemas no fluxo da venda, pois
            # cancelar o picking não cancela efetivamente o *efeito*
            # do procurement, e o core interpreta a alteração da
            # quantidade pedida de forma incorreta
            #
            self.env.cr.execute(
                'delete from procurement_order where group_id = %(group_id)s',
                {'group_id': picking.group_id.id}
            )
