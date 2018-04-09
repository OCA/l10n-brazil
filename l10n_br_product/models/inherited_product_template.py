# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm
from odoo.addons.l10n_br_base.constante_tributaria import (
    ORIGEM_MERCADORIA,
    TIPO_PRODUTO_SERVICO,
    TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO,
    TIPO_PRODUTO_SERVICO_SERVICOS,
)

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(
        selection_add=[
            ('product', 'Stockable Product'),
        ]
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
    preco_transferencia = fields.Monetary(
        string='Preço de transferência',
    )
    marca = fields.Char(
        string='Marca',
        size=60
    )
    #
    # Para a automação dos volumes na NF-e
    #
    volume = fields.Float(
        string='Volume líquido',
    )
    weight = fields.Float(
        string='Peso líquido',
    )
    weight_gross = fields.Float(
        string='Peso bruto',
    )
    codigo_barras_tributacao = fields.Char(
        string='Código de barras para tributação comercial',
        size=14,
        index=True,
    )
    unidade_tributacao_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unidade para tributação comercial',
    )
    fator_conversao_unidade_tributacao = fields.Float(
        string='Fator de conversão entre as unidades',
        default=1,
    )

    def _valida_codigo_barras(self):
        self.ensure_one()

        if self.barcode:
            if (not self.env['barcode.nomenclature'].check_ean(self.barcode)):
                raise ValidationError(_('Código de barras inválido!'))

        if self.codigo_barras_tributacao:
            if (not self.env['barcode.nomenclature'].check_ean(
                    self.codigo_barras_tributacao)):
                raise ValidationError(
                    _('Código de barras para tributação comercial inválido!'))

    @api.constrains('barcode', 'codigo_barras_tributacao')
    def _constrains_codigo_barras(self):
        for produto in self:
            produto._valida_codigo_barras()

    @api.onchange('barcode', 'codigo_barras_tributacao')
    def onchange_codigo_barras(self):
        return self._valida_codigo_barras()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductTemplate, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        #
        # Remove a view "estoque" utilizada pelo emissor de nf-e quando
        # o módulo stock do core esta instalado, para evitar conflitos
        #
        if (self.env['ir.module.module'].search_count([
            ('name', '=', 'stock'),
            ('state', '=', 'installed')
        ]) and res.get('type') == 'form'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//page[@name='estoque']"):
                node.getparent().remove(node)
            res['arch'] = etree.tostring(doc)
        return res


    # nome_unico = fields.Char(
    #     string='Nome',
    #     size=120,
    #     index=True,
    #     compute='_compute_nome_unico',
    #     store=True,
    # )
    # codigo_unico = fields.Char(
    #     string='Código',
    #     size=60,
    #     index=True,
    #     compute='_compute_codigo_unico',
    #     store=True
    # )
    # codigo_cliente = fields.Char(
    #     string='Código do cliente',
    #     size=60,
    #     index=True,
    # )

    # @api.depends('codigo')
    # def _compute_codigo_unico(self):
    #     for record in self:
    #         codigo_unico = record.codigo or ''
    #         codigo_unico = codigo_unico.lower().strip()
    #         codigo_unico = codigo_unico.replace(' ', ' ')
    #         codigo_unico = codigo_unico.replace('²', '2')
    #         codigo_unico = codigo_unico.replace('³', '3')
    #         codigo_unico = punctuation_rm(codigo_unico)
    #         record.codigo_unico = codigo_unico
    #
    # @api.depends('nome')
    # def _compute_nome_unico(self):
    #     for record in self:
    #         nome_unico = record.nome or ''
    #         nome_unico = nome_unico.lower().strip()
    #         nome_unico = nome_unico.replace(' ', ' ')
    #         nome_unico = nome_unico.replace('²', '2')
    #         nome_unico = nome_unico.replace('³', '3')
    #         nome_unico = punctuation_rm(nome_unico)
    #         record.nome_unico = nome_unico

    # @api.constrains('codigo')
    # def _check_codigo(self):
    #     for record in self:
    #         if record.id:
    #             produto_ids = self.search([
    #                 ('codigo_unico', '=', record.codigo_unico),
    #                 ('id', '!=', record.id)
    #             ])
    #         else:
    #             produto_ids = self.search([
    #                 ('codigo_unico', '=', record.codigo_unico)
    #             ])
    #
    #         if len(produto_ids) > 0:
    #             raise ValidationError('Código de produto já existe!')
    #
    # @api.constrains('nome')
    # def _check_nome(self):
    #     for produto in self:
    #         if produto.id:
    #             produto_ids = self.search(
    #                 [('nome_unico', '=', produto.nome_unico),
    #                  ('id', '!=', produto.id)])
    #         else:
    #             produto_ids = self.search(
    #                 [('nome_unico', '=', produto.nome_unico)])
    #
    #         if len(produto_ids) > 0:
    #             raise ValidationError('Nome de produto já existe!')

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
    #         args += [
    #             '|',
    #             ['codigo', operator, name],
    #             '|',
    #             ['codigo_unico', operator, name.lower()],
    #             '|',
    #             ['barcode', '=', name],
    #             '|',
    #             ['nome', operator, name],
    #             ['nome_unico', operator, name.lower()],
    #         ]
    #         produtos = self.search(args, limit=limit)
    #         return produtos.name_get()
    #
    #     return super(ProductTemplate, self).name_search(name=name, args=args,
    #                                             operator=operator, limit=limit)
    #
    # @api.depends('unidade_tributacao_ncm_id', 'unidade_id')
    # def _compute_exige_fator_conversao_ncm(self):
    #     for produto in self:
    #         if produto.unidade_id and produto.unidade_tributacao_ncm_id:
    #             produto.exige_fator_conversao_unidade_tributacao_ncm = (
    #                 produto.unidade_id.id !=
    #                 produto.unidade_tributacao_ncm_id.id
    #             )
    #         else:
    #             produto.exige_fator_conversao_unidade_tributacao_ncm = False
    #             produto.fator_conversao_unidade_tributacao_ncm = 1
