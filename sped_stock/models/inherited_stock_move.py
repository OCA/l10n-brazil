# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class StockMove(SpedCalculoImpostoItem, models.Model):
    _inherit = 'stock.move'
    _abstract = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='picking_id.is_brazilian',
    )
    #
    # O campo documento_id serve para que a classe SpedCalculoImpostoItem
    # saiba qual o cabeçalho do documento (venda, compra, NF etc.)
    # tem as definições da empresa, participante, data de emissão etc.
    # necessárias aos cálculos dos impostos;
    # Uma vez definido o documento, a operação pode variar entre produto e
    # serviço, por isso o compute no campo; a data de emissão também vem
    # trazida do campo correspondente no model que estamos tratando no momento
    #
    documento_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Transferência de Estoque',
        related='picking_id',
        readonly=True,
    )
    data_emissao = fields.Datetime(
        string='Data de emissão',
        related='documento_id.date',
        readonly=True,
    )
    documento_item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='stock_move_id',
        string='Itens dos Documentos Fiscais',
        copy=False,
    )

    data = fields.Date(
        string='Data',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    sped_documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )
    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string='Item do Documento Fiscal',
        ondelete='restrict',
    )


    @api.depends('date')
    def _compute_data_hora_separadas(self):
        for move in self:
            data, hora = self._separa_data_hora(move.date)
            move.data = data
            #move.hora = hora

    def _onchange_produto_id_emissao_propria(self):
        self.ensure_one()

        if not (self.picking_id and self.picking_id.operacao_id):
            return

        return super(StockMove, self)._onchange_produto_id_emissao_propria()

    def prepara_dados_documento_item(self):
        self.ensure_one()

        return {
            'stock_move_id': self.id,
            'vr_unitario': self.price_unit,
        }

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(StockMove, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(StockMove, self).write(dados)

    def product_price_update_after_done(self):
        pass

    def product_price_update_before_done(self):
        pass

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        return []
