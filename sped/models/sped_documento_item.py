# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.addons.l10n_br_base.constante_tributaria import (
    REGIME_TRIBUTARIO,
    MODELO_FISCAL,
    IE_DESTINATARIO,
    TIPO_EMISSAO,
    ENTRADA_SAIDA,
    TIPO_CONSUMIDOR_FINAL,
)
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import \
    SpedCalculoImpostoItem


_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItem(SpedCalculoImpostoItem, models.Model):
    _name = b'sped.documento.item'
    _description = 'Itens do Documento Fiscal'
    _abstract = False
    # _order = 'emissao, modelo, data_emissao desc, serie, numero'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento',
        ondelete='cascade',
        required=True,
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        related='documento_id.regime_tributario',
        readonly=True,
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL,
        string='Modelo',
        related='documento_id.modelo',
        readonly=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='documento_id.empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='documento_id.participante_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        related='documento_id.operacao_id',
        readonly=True,
    )
    contribuinte = fields.Selection(
        selection=IE_DESTINATARIO,
        string='Contribuinte',
        related='participante_id.contribuinte',
        readonly=True,
    )
    emissao = fields.Selection(
        selection=TIPO_EMISSAO,
        string='Tipo de emissão',
        related='documento_id.emissao',
        readonly=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='documento_id.data_emissao',
        readonly=True,
    )
    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        string='Entrada/saída',
        related='documento_id.entrada_saida',
        readonly=True,
    )
    consumidor_final = fields.Selection(
        selection=TIPO_CONSUMIDOR_FINAL,
        string='Tipo do consumidor',
        related='documento_id.consumidor_final',
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

    cst_icms_readonly = fields.Char(
        string='CST ICMS',
        compute='_sync_cst_icms',
    )

    @api.depends('cst_icms')
    def _sync_cst_icms(self):
        for item in self:
            if not item.cst_icms:
                continue
            item.cst_icms_readonly = item.cst_icms

    cst_pis_readonly = fields.Char(
        string='CST PIS',
        compute='_sync_cst_pis',
    )

    @api.depends('cst_pis')
    def _sync_cst_pis(self):
        for item in self:
            if not item.cst_pis:
                continue
            item.cst_pis_readonly = item.cst_pis

    cst_cofins_readonly = fields.Char(
        string='CST COFINS',
        compute='_sync_cst_cofins',
    )

    @api.depends('cst_cofins')
    def _sync_cst_cofins(self):
        for item in self:
            if not item.cst_cofins:
                continue
            item.cst_cofins_readonly = item.cst_cofins

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

    def _set_additional_fields(self, sped_documento_id):
        pass

    def _renderizar_informacoes_template(
            self, dados_infcomplementar, infcomplementar):

        try:
            template = TemplateBrasil(infcomplementar.encode('utf-8'))
            informacao_complementar = template.render(**dados_infcomplementar)
        except Exception as e:
            raise UserError(
                _(""" Erro ao gerar informação adicional do item"""))
        return informacao_complementar.decode('utf-8')