# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia -
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

import logging
from ..constante_tributaria import (
    ORIGEM_MERCADORIA,
    TIPO_PRODUTO_SERVICO,
    TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO,
    TIPO_PRODUTO_SERVICO_SERVICOS,
)
_logger = logging.getLogger(__name__)

try:
    from pybrasil.produto import valida_ean

except (ImportError, IOError) as err:
    _logger.debug(err)


class Produto(models.Model):
    _description = u'Produtos e serviços'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _name = 'sped.produto'
    _order = 'codigo, nome'
    _rec_name = 'nome'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string=u'Product original',
        ondelete='restrict',
        required=True,
    )
    # company_id = fields.Many2one(
    # 'res.company', string=u'Empresa', ondelete='restrict')
    nome = fields.Char(
        string=u'Nome',
        size=120,
        index=True,
    )
    codigo = fields.Char(
        string=u'Código',
        size=60,
        index=True,
    )
    codigo_barras = fields.Char(
        string=u'Código de barras',
        size=14,
        index=True,
    )
    marca = fields.Char(
        string=u'Marca',
        size=60
    )
    preco_venda = fields.Float(
        string=u'Preço de venda',
        digits=dp.get_precision('SPED - Valor Unitário')
    )
    preco_custo = fields.Float(
        string=u'Preço de custo',
        digits=dp.get_precision('SPED - Valor Unitário')
    )
    peso_bruto = fields.Float(
        string=u'Peso bruto',
        digits=(18, 4)
    )
    peso_liquido = fields.Float(
        string=u'Peso líquido',
        digits=(18, 4)
    )
    tipo = fields.Selection(
        selection=TIPO_PRODUTO_SERVICO,
        string=u'Tipo',
        index=True
    )
    org_icms = fields.Selection(
        selection=ORIGEM_MERCADORIA,
        string=u'Origem da mercadoria',
        default='0'
    )
    ncm_id = fields.Many2one(
        comodel_name='sped.ncm',
        string=u'NCM')
    cest_ids = fields.Many2many(
        comodel_name='sped.cest',
        related='ncm_id.cest_ids',
        string=u'Códigos CEST',
    )
    exige_cest = fields.Boolean(
        string=u'Exige código CEST?',
    )
    cest_id = fields.Many2one(
        comodel_name='sped.cest',
        string=u'CEST'
    )
    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string=u'Protocolo/Convênio',
    )
    al_ipi_id = fields.Many2one(
        comodel_name='sped.aliquota.ipi',
        string=u'Alíquota de IPI',
    )
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string=u'Alíquota de PIS e COFINS',
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string=u'Código do serviço',
    )
    nbs_id = fields.Many2one(
        comodel_name='sped.nbs',
        string=u'NBS',
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string=u'Unidade',
    )
    unidade_tributacao_ncm_id = fields.Many2one(
        comodel_name='sped.unidade',
        related='ncm_id.unidade_id',
        string=u'Unidade de tributação do NCM',
        readonly=True,
    )
    fator_conversao_unidade_tributacao_ncm = fields.Float(
        string=u'Fator de conversão entre as unidades',
        default=1,
    )
    exige_fator_conversao_unidade_tributacao_ncm = fields.Boolean(
        string=u'Exige fator de conversão entre as unidades?',
        compute='_compute_exige_fator_conversao_ncm',
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

        valores = {}
        res = {'value': valores}

        if self.codigo_barras:
            if (not valida_ean(self.codigo_barras)):
                raise ValidationError(u'Código de barras inválido!')

            valores['codigo_barras'] = self.codigo_barras

        return res

    @api.constrains('codigo_barras')
    def _constrains_codigo_barras(self):
        for produto in self:
            produto._valida_codigo_barras()

    @api.onchange('codigo_barras')
    def onchange_codigo_barras(self):
        return self._valida_codigo_barras()

    @api.onchange('ncm_id')
    def onchange_ncm(self):
        if len(self.ncm_id.cest_ids) == 1:
            return {'value': {
                'cest_id': self.ncm_id.cest_ids[0].id,
                'exige_cest': True
            }}

        elif len(self.ncm_id.cest_ids) > 1:
            return {'value': {
                'cest_id': False,
                'exige_cest': True
            }}

        else:
            return {'value': {
                'cest_id': False,
                'exige_cest': False
            }}

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

        produto = super(Produto, self).create(dados)
        produto.sync_to_product()

        return produto

    @api.multi
    def write(self, dados):
        res = super(Produto, self).write(dados)
        self.sync_to_product()
        return res
