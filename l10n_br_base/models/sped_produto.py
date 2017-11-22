# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia -
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp
from .sped_base import SpedBase
from ..constante_tributaria import (
    ORIGEM_MERCADORIA,
    TIPO_PRODUTO_SERVICO,
    TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO,
    TIPO_PRODUTO_SERVICO_SERVICOS,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.produto import valida_ean
    from pybrasil.base import tira_acentos

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedProduto(SpedBase, models.Model):
    _name = b'sped.produto'
    _description = 'Produtos e serviços'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _order = 'nome, codigo'
    _rec_name = 'nome'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product original',
        ondelete='restrict',
        required=True,
    )
    # company_id = fields.Many2one(
    # 'res.company', string='Empresa', ondelete='restrict')
    nome = fields.Char(
        string='Nome',
        size=120,
        index=True,
    )
    nome_unico = fields.Char(
        string='Nome',
        size=120,
        index=True,
        compute='_compute_nome_unico',
        store=True,
    )
    codigo = fields.Char(
        string='Código',
        size=60,
        index=True,
    )
    codigo_unico = fields.Char(
        string='Código',
        size=60,
        index=True,
        compute='_compute_codigo_unico',
        store=True
    )
    codigo_cliente = fields.Char(
        string='Código do cliente',
        size=60,
        index=True,
    )
    codigo_barras = fields.Char(
        string='Código de barras',
        size=14,
        index=True,
    )
    marca = fields.Char(
        string='Marca',
        size=60
    )
    preco_venda = fields.Monetary(
        string='Preço de venda',
        currency_field='currency_unitario_id',
    )
    preco_custo = fields.Monetary(
        string='Preço de custo',
        currency_field='currency_unitario_id',
    )
    preco_transferencia = fields.Monetary(
        string='Preço de transferência',
        currency_field='currency_unitario_id',
    )
    peso_bruto = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
    )
    peso_liquido = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
    )
    tipo = fields.Selection(
        selection=TIPO_PRODUTO_SERVICO,
        string='Tipo',
        index=True
    )
    org_icms = fields.Selection(
        selection=ORIGEM_MERCADORIA,
        string='Origem da mercadoria',
        default='0'
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
    )
    currency_unidade_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade (símbolo)',
        related='unidade_id.currency_id',
        readonly=True,
    )
    codigo_barras_tributacao = fields.Char(
        string='Código de barras para tributação comercial',
        size=14,
        index=True,
    )
    unidade_tributacao_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade para tributação comercial',
    )
    currency_unidade_tributacao_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade para tributação comercial (símbolo)',
        related='unidade_tributacao_id.currency_id',
        readonly=True,
    )
    fator_conversao_unidade_tributacao = fields.Float(
        string='Fator de conversão entre as unidades',
        default=1,
    )
    #
    # Para a automação dos volumes na NF-e
    #
    especie = fields.Char(
        string='Espécie/embalagem',
        size=60,
    )
    fator_quantidade_especie = fields.Float(
        string='Quantidade por espécie/embalagem',
        digits=dp.get_precision('SPED - Quantidade'),
    )
    #
    # Novos campos da NF-e 4.00
    #
    produzido_escala_relevante = fields.Boolean(
        string='Produzido em escala relevante?',
        default=True,
    )
    fabricante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Fabricante',
        ondelete='restrict',
    )
    codigo_beneficio_fiscal = fields.Char(
        string='Código do benefício fiscal',
        size=20,
    )


    @api.depends('ncm_id', 'unidade_id')
    def _compute_exige_fator_conversao_ncm(self):
        for produto in self:
            if produto.unidade_id and produto.unidade_tributacao_ncm_id:
                produto.exige_fator_conversao_unidade_tributacao_ncm = (
                    produto.unidade_id.id !=
                    produto.unidade_tributacao_ncm_id.id
                )
            else:
                produto.exige_fator_conversao_unidade_tributacao_ncm = False
                produto.fator_conversao_unidade_tributacao_ncm = 1

    def _valida_codigo_barras(self):
        self.ensure_one()

        if self.codigo_barras:
            if (not valida_ean(self.codigo_barras)):
                raise ValidationError(_('Código de barras inválido!'))

        if self.codigo_barras_tributacao:
            if (not valida_ean(self.codigo_barras_tributacao)):
                raise ValidationError(
                    _('Código de barras para tributação comercial inválido!'))

    @api.constrains('codigo_barras', 'codigo_barras_tributacao')
    def _constrains_codigo_barras(self):
        for produto in self:
            produto._valida_codigo_barras()

    @api.onchange('codigo_barras', 'codigo_barras_tributacao')
    def onchange_codigo_barras(self):
        return self._valida_codigo_barras()

    @api.depends('codigo')
    def _compute_codigo_unico(self):
        for produto in self:
            codigo_unico = produto.codigo or ''
            codigo_unico = codigo_unico.lower().strip()
            codigo_unico = codigo_unico.replace(' ', ' ')
            codigo_unico = codigo_unico.replace('²', '2')
            codigo_unico = codigo_unico.replace('³', '3')
            codigo_unico = tira_acentos(codigo_unico)
            produto.codigo_unico = codigo_unico

    @api.depends('nome')
    def _compute_nome_unico(self):
        for produto in self:
            nome_unico = produto.nome or ''
            nome_unico = nome_unico.lower().strip()
            nome_unico = nome_unico.replace(' ', ' ')
            nome_unico = nome_unico.replace('²', '2')
            nome_unico = nome_unico.replace('³', '3')
            nome_unico = tira_acentos(nome_unico)
            produto.nome_unico = nome_unico

    @api.constrains('codigo')
    def _check_codigo(self):
        for produto in self:
            if produto.id:
                produto_ids = self.search([
                    ('codigo_unico', '=', produto.codigo_unico),
                    ('id', '!=', produto.id)
                ])
            else:
                produto_ids = self.search([
                    ('codigo_unico', '=', produto.codigo_unico)
                ])

            if len(produto_ids) > 0:
                raise ValidationError('Código de produto já existe!')

    @api.constrains('nome')
    def _check_nome(self):
        for produto in self:
            if produto.id:
                produto_ids = self.search(
                    [('nome_unico', '=', produto.nome_unico),
                     ('id', '!=', produto.id)])
            else:
                produto_ids = self.search(
                    [('nome_unico', '=', produto.nome_unico)])

            if len(produto_ids) > 0:
                raise ValidationError('Nome de produto já existe!')

    def prepare_sync_to_product(self):
        self.ensure_one()

        dados = {
            'name': self.nome,
            'default_code': self.codigo,
            'active': True,
            'weight': self.peso_liquido,
            'uom_id': self.unidade_id.uom_id.id,
            'uom_po_id': self.unidade_id.uom_id.id,
            'standard_price': self.preco_custo,
            'list_price': self.list_price,
            'sale_ok': True,
            'purchase_ok': True,
            'barcode': self.codigo_barras,
            'sped_produto_id': self.id,
        }

        if self.tipo == TIPO_PRODUTO_SERVICO_SERVICOS:
            dados['type'] = 'service'

        elif self.tipo == TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO:
            dados['type'] = 'consu'

        else:
            dados['type'] = 'product'

        return dados

    @api.multi
    def sync_to_product(self):
        for produto in self:
            dados = produto.prepare_sync_to_product()
            produto.product_id.write(dados)

    @api.model
    def create(self, dados):
        dados['name'] = dados['nome']
        dados['default_code'] = dados['codigo']

        produto = super(SpedProduto, self).create(dados)
        produto.sync_to_product()

        return produto

    @api.multi
    def write(self, dados):
        res = super(SpedProduto, self).write(dados)
        self.sync_to_product()
        return res

    @api.multi
    def name_get(self):
        res = []

        for produto in self:
            nome = '['
            nome += produto.codigo
            nome += '] '
            nome += produto.nome
            res.append((produto.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            args += [
                '|',
                ['codigo', operator, name],
                '|',
                ['codigo_unico', operator, name.lower()],
                '|',
                ['codigo_barras', '=', name],
                '|',
                ['nome', operator, name],
                ['nome_unico', operator, name.lower()],
            ]
            produtos = self.search(args, limit=limit)
            return produtos.name_get()

        return super(SpedProduto, self).name_search(name=name, args=args,
                                                operator=operator, limit=limit)
