# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.produto import valida_ean

except (ImportError, IOError) as err:
    _logger.debug(err)

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from ..constante_tributaria import *


class Produto(models.Model):
    _description = 'Produtos e serviços'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _name = 'sped.produto'
    _order = 'codigo, nome'
    _rec_name = 'nome'

    product_id = fields.Many2one('product.product', 'Product original', ondelete='restrict', required=True)

    #company_id = fields.Many2one('res.company', string='Empresa', ondelete='restrict')
    nome = fields.NameChar(string='Nome', size=120, index=True)
    codigo = fields.Char(string='Código', size=60, index=True)
    codigo_barras = fields.Char(string='Código de barras', size=14, index=True)
    marca = fields.NameChar(string='Marca', size=60)

    preco_venda = fields.Float('Preço de venda', digits=dp.get_precision('SPED - Valor Unitário'))
    preco_custo = fields.Float('Preço de custo', digits=dp.get_precision('SPED - Valor Unitário'))
    peso_bruto = fields.Float('Peso bruto', digits=(18, 4))
    peso_liquido = fields.Float('Peso líquido', digits=(18, 4))

    tipo = fields.Selection(TIPO_PRODUTO_SERVICO, string='Tipo', index=True)

    org_icms = fields.Selection(ORIGEM_MERCADORIA, string='Origem da mercadoria', default='0')

    ncm_id = fields.Many2one('sped.ncm', 'NCM')
    cest_ids = fields.Many2many('sped.cest', related='ncm_id.cest_ids', string='Códigos CEST')

    exige_cest = fields.Boolean('Exige código CEST?')
    cest_id = fields.Many2one('sped.cest', 'CEST')
    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo/Convênio')
    al_ipi_id = fields.Many2one('sped.aliquota.ipi', 'Alíquota de IPI')
    al_pis_cofins_id = fields.Many2one('sped.aliquota.pis.cofins', 'Alíquota de PIS e COFINS')

    servico_id = fields.Many2one('sped.servico', 'Código do serviço')
    nbs_id = fields.Many2one('sped.nbs', 'NBS')

    unidade_id = fields.Many2one('sped.unidade', 'Unidade')
    unidade_tributacao_ncm_id = fields.Many2one('sped.unidade', related='ncm_id.unidade_id', string='Unidade de tributação do NCM', readonly=True)
    fator_conversao_unidade_tributacao_ncm = fields.Float('Fator de conversão entre as unidades', default=1)
    exige_fator_conversao_unidade_tributacao_ncm = fields.Boolean('Exige fator de conversão entre as unidades?', compute='_compute_exige_fator_conversao_ncm')

    @api.depends('ncm_id', 'unidade_id')
    def _compute_exige_fator_conversao_ncm(self):
        for produto in self:
            if produto.unidade_id and produto.unidade_tributacao_ncm_id:
                produto.exige_fator_conversao_unidade_tributacao_ncm = produto.unidade_id.id != produto.unidade_tributacao_ncm_id.id
            else:
                produto.exige_fator_conversao_unidade_tributacao_ncm = False
                produto.fator_conversao_unidade_tributacao_ncm = 1

    def _valida_codigo_barras(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.codigo_barras:
            if (not valida_ean(self.codigo_barras)):
                raise ValidationError('Código de barras inválido!')

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
            return {'value': {'cest_id': self.ncm_id.cest_ids[0].id, 'exige_cest': True}}

        elif len(self.ncm_id.cest_ids) > 1:
            return {'value': {'cest_id': False, 'exige_cest': True}}

        else:
            return {'value': {'cest_id': False, 'exige_cest': False}}

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
