# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)



class SaleOrderLine(SpedCalculoImpostoItem, models.Model):
    _inherit = 'sale.order.line'
    _abstract = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='order_id.is_brazilian',
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
        comodel_name='sale.order',
        string='Pedido de venda',
        related='order_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        _compute='_onchange_produto_id',
        store=True,
    )
    data_emissao = fields.Datetime(
        string='Data de emissão',
        related='documento_id.date_order',
        readonly=True,
    )

    #
    # Campos readonly
    #
    unidade_readonly_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
        ondelete='restrict',
        compute='_compute_readonly',
    )
    unidade_tributacao_readonly_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade para tributação',
        ondelete='restrict',
        compute='_compute_readonly',
    )
    vr_produtos_readonly = fields.Monetary(
        string='Valor do produto/serviço',
        compute='_compute_readonly',
    )
    vr_produtos_tributacao_readonly = fields.Monetary(
        string='Valor do produto/serviço para tributação',
        compute='_compute_readonly',
    )
    vr_operacao_readonly = fields.Monetary(
        string='Valor da operação',
        compute='_compute_readonly',
    )
    vr_operacao_tributacao_readonly = fields.Monetary(
        string='Valor da operação para tributação',
        compute='_compute_readonly',
    )
    vr_nf_readonly = fields.Monetary(
        string='Valor da NF',
        compute='_compute_readonly',
    )
    vr_fatura_readonly = fields.Monetary(
        string='Valor da fatura',
        compute='_compute_readonly',
    )
    vr_unitario_custo_comercial_readonly = fields.Float(
        string='Custo unitário comercial',
        compute='_compute_readonly',
        digits=dp.get_precision('SPED - Valor Unitário'),
    )
    vr_custo_comercial_readonly = fields.Monetary(
        string='Custo comercial',
        compute='_compute_readonly',
    )
    peso_bruto_readonly = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
        compute='_compute_readonly',
    )
    peso_liquido_readonly = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
        compute='_compute_readonly',
    )
    quantidade_especie_readonly = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
        compute='_compute_readonly',
    )
    permite_alteracao = fields.Boolean(
        string='Permite alteração?',
        compute='_compute_permite_alteracao',
    )

    sped_documento_item_ids = fields.One2many(
        comodel_name='sped.documento.item',
        inverse_name='sale_order_line_id',
        string='Itens dos Documentos Fiscais',
        copy=False,
    )

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        for item in self:
            if not item.order_id:
                item.operacao_id = False

            if not item.produto_id:
                item.operacao_id = False

            if item.produto_id.tipo == TIPO_PRODUTO_SERVICO_SERVICOS:
                if item.order_id.sped_operacao_servico_id:
                    item.operacao_id = item.order_id.sped_operacao_servico_id
            else:
                if item.order_id.sped_operacao_produto_id:
                    item.operacao_id = item.order_id.sped_operacao_produto_id

            if not item.data_emissao:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'Por favor, defina a data do pedido \n'
                        'para permtir o cálculo correto dos impostos'),
                }
                return {'warning': warning}

            if not item.operacao_id:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'Por favor, defina a operação fiscal \n'
                        'para permitir o cálculo correto dos impostos'),
                }
                return {'warning': warning}

            item.name = item.produto_id.nome
            item.produto_descricao = item.produto_id.nome
            item.product_id = item.produto_id.product_id
            item.price_unit = item.produto_id.preco_venda
            item.vr_unitario = item.produto_id.preco_venda

        super(SaleOrderLine, self)._onchange_produto_id()

    # @api.onchange('price_unit', 'product_uom_qty')
    # def _onchange_price_unit_product_uom_qty(self):
    #     for item in self:
    #         # if item.is_brazilian:
    #         item.vr_unitario = item.price_unit
    #         item.quantidade = item.product_uom_qty

    @api.onchange('vr_unitario', 'quantidade')
    def _onchange_vr_unitario(self):
        for item in self:
            item.price_unit = item.vr_unitario
            item.product_uom_qty = item.quantidade
            item.product_uom = item.unidade_id.uom_id

    @api.depends('modelo', 'emissao')
    def _compute_permite_alteracao(self):
        for item in self:
            item.permite_alteracao = True

    @api.depends('unidade_id', 'unidade_tributacao_id',
                 'vr_produtos', 'vr_operacao',
                 'vr_produtos_tributacao', 'vr_operacao_tributacao',
                 'vr_nf', 'vr_fatura',
                 'vr_unitario_custo_comercial', 'vr_custo_comercial')
    def _compute_readonly(self):
        for item in self:
            item.unidade_readonly_id = \
                item.unidade_id.id if item.unidade_id else False
            if item.unidade_tributacao_id:
                item.unidade_tributacao_readonly_id = \
                    item.unidade_tributacao_id.id
            else:
                item.unidade_tributacao_readonly_id = False

            item.vr_produtos_readonly = item.vr_produtos
            item.vr_operacao_readonly = item.vr_operacao
            item.vr_produtos_tributacao_readonly = item.vr_produtos_tributacao
            item.vr_operacao_tributacao_readonly = item.vr_operacao_tributacao
            item.vr_nf_readonly = item.vr_nf
            item.vr_fatura_readonly = item.vr_fatura
            item.vr_unitario_custo_comercial_readonly = \
                item.vr_unitario_custo_comercial
            item.vr_custo_comercial_readonly = item.vr_custo_comercial
            item.peso_bruto_readonly = item.peso_bruto
            item.peso_liquido_readonly = item.peso_liquido
            item.quantidade_especie_readonly = item.quantidade_especie

    @api.multi
    def _prepare_invoice_line(self, qty):
        """ """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.is_brazilian:
            res['produto_id'] = self.produto_id.id
            res['quantidade'] = self.quantidade
            res['vr_unitario'] = self.vr_unitario
            res['vr_desconto'] = self.vr_desconto
            res['unidade_id'] = self.unidade_id.id
            res['protocolo_id'] = self.protocolo_id.id
            res['operacao_item_id'] = self.operacao_item_id.id
            res['unidade_id'] = self.unidade_id.id
            res['vr_seguro'] = self.vr_seguro
            res['vr_outras'] = self.vr_outras
            res['vr_frete'] = self.vr_frete
        return res

    def prepara_dados_sped_documento_item(self):
        self.ensure_one()

        return {
            'sale_order_line_id': self.id,
        }

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity',
                 'sped_documento_item_ids.quantidade')
    def _get_invoice_qty(self):
        for item in self:
            if not item.order_id.is_brazilian:
                super(SaleOrderLine, self)._get_invoice_qty()
                continue

            sped_documento_item_ids = item.sped_documento_item_ids.search(
                [('documento_id.situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            qty_invoiced = 0.0
            for documento_item in sped_documento_item_ids:
                qty_invoiced += documento_item.quantidade

            item.qty_invoiced = qty_invoiced
