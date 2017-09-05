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
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)



class AccountInvoiceLine(SpedCalculoImpostoItem, models.Model):
    _inherit = 'account.invoice.line'
    _abstract = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='invoice_id.is_brazilian',
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
        comodel_name='account.invoice',
        string='Fatura',
        related='invoice_id',
        readonly=True,
    )

    vr_nf = fields.Monetary(
        compute='_amount_price_brazil'
    )
    vr_fatura = fields.Monetary(
        compute='_amount_price_brazil'
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='invoice_id.empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='invoice_id.participante_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        _compute='_onchange_produto_id',
        store=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='documento_id.date',
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

    # documento_item_ids = fields.One2many(
    #     comodel_name='sped.documento.item',
    #     inverse_name='account_invoice_line_id',
    #     string='Itens dos Documentos Fiscais',
    #     copy=False,
    # )

    @api.onchange('produto_id')
    def _onchange_produto_id(self):
        for item in self:
            if not item.invoice_id:
                item.operacao_id = False

            if not item.produto_id:
                item.operacao_id = False

            if item.produto_id.tipo == TIPO_PRODUTO_SERVICO_SERVICOS:
                if item.invoice_id.operacao_servico_id:
                    item.operacao_id = item.invoice_id.operacao_servico_id
            else:
                if item.invoice_id.operacao_produto_id:
                    item.operacao_id = item.invoice_id.operacao_produto_id

            if not item.data_emissao:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'Por favor, defina a data da fatura \n'
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

        super(AccountInvoiceLine, self)._onchange_produto_id()

    @api.onchange('vr_unitario', 'quantidade')
    def _onchange_vr_unitario(self):
        for item in self:
            item.price_unit = item.vr_unitario
            item.quantity = item.quantidade
            item.product_uom = item.unidade_id.uom_id

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

    def prepara_dados_documento_item(self):
        self.ensure_one()

        return {
            # 'account_invoice_line_id': self.id,
        }

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(AccountInvoiceLine, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(AccountInvoiceLine, self).write(dados)

    #@api.one
    #@api.depends(
        #'price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        #'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        #'invoice_id.company_id', 'invoice_id.date_invoice',
        ##
        ## Campos brasileiros
        ##
        #'produto_id',
        #'quantidade',
        #'vr_unitario',
        #'vr_desconto',
        #'unidade',
        #'operacao_id',
        #'operacao_item_id',
        #'protocolo_id',
        ## TODO: Outros campos que precisamos monitorar
    #)
    #def _compute_price(self):
        #super(AccountInvoiceLine, self)._compute_price()
        #if self.is_brazilian:
             #self._amount_price_brazil()
