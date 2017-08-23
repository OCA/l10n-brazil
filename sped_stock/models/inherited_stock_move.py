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


class SpedStockMove(SpedCalculoImpostoItem, models.Model):
    _inherit = 'stock.move'
    _abstract = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='picking_id.is_brazilian',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='picking_id.sped_empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='picking_id.sped_participante_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        related='picking_id.sped_operacao_produto_id',
        readonly=True,
    )

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        #
        # SOBREESCREVEMOS ESSE MÉTODO POIS O CORE NAO PERMITE SE ALTERAR O
        # CAMPO product_id APÓS O PICKING SER CONFIRMADO
        #
        return

    @api.multi
    @api.onchange('produto_id', 'product_id')
    def onchange_product_id_date(self):
        for record in self:
            if not record.product_id and not record.produto_id:
                return False
            if not record.operacao_id:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'Por favor defina a operação'),
                }
                return {'warning': warning}

            if record.produto_id and not record.product_id:
                record.product_id = record.produto_id.product_id
            if record.product_id and not record.produto_id:
                record.produto_id = record.produto_id.search(
                    [('product_id', '=', record.product_id.id)]
                )

    @api.model
    def create(self, vals):
        res = super(SpedStockMove, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            super(SpedStockMove, record).write(vals)

    @api.multi
    def _prepare_sped_line(self):
        """ """
        self.calcula_impostos()
        res = {
            'produto_id': self.produto_id.id,
            'quantidade':  self.quantidade or self.quantity,
            'vr_unitario': self.vr_unitario or self.produto_id.preco_venda,
            'vr_desconto': self.vr_desconto,
            'unidade_id': self.unidade_id.id,
            'protocolo_id': self.protocolo_id.id,
            'operacao_item_id': self.operacao_item_id.id,
            'vr_seguro': self.vr_seguro,
            'vr_outras': self.vr_outras,
            'vr_frete': self.vr_frete,
        }
        return res
