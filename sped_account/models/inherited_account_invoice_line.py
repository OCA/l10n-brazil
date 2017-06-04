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
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    REGIME_TRIBUTARIO,
    MODELO_FISCAL,
    IE_DESTINATARIO,
    TIPO_EMISSAO,
    ENTRADA_SAIDA,
    TIPO_CONSUMIDOR_FINAL,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string=u'Item do Documento Fiscal',
        ondelete='cascade',
    )
    is_brazilian_invoice = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='invoice_id.is_brazilian_invoice',
    )

    # @api.multi
    # def _check_brazilian_invoice(self, operation):
    #     for item in self:
    #         if (item.is_brazilian_invoice and
    #                 'sped_documento_item_id' not in self._context):
    #             if operation == 'create':
    #                 raise ValidationError(
    #                     'This is a Brazilian Invoice! You should create it '
    #                     'through the proper Brazilian Fiscal Document!')
    #             elif operation == 'write':
    #                 raise ValidationError(
    #                     'This is a Brazilian Invoice! You should change it '
    #                     'through the proper Brazilian Fiscal Document!')
    #             elif operation == 'unlink':
    #                 raise ValidationError(
    #                     'This is a Brazilian Invoice! You should delete it '
    #                     'through the proper Brazilian Fiscal Document!')

    # @api.multi
    # def create(self, dados):
    #     invoice = super(AccountInvoiceLine, self).create(dados)
    #     invoice._check_brazilian_invoice()
    #     return invoice
    #
    # @api.multi
    # def write(self, dados):
    #     self._check_brazilian_invoice()
    #     res = super(AccountInvoiceLine, self).write(dados)
    #     return res
    #
    # @api.multi
    # def unlink(self):
    #     self._check_brazilian_invoice()
    #     res = super(AccountInvoiceLine, self).unlink()
    #     return res



class AccountInvoiceLineBrazil(models.Model):
    _name = b'account.invoice.line.brazil'
    _description = 'Linhas da Fatura'
    _inherit = 'sped.calculo.imposto'
    _abstract = False



class AccountInvoiceLineBrazil2(models.Model):
    _inherit = 'account.invoice.line.brazil'
    _inherits = {'account.invoice.line': 'invoice_line_id'}

    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Invoice Line original',
        ondelete='restrict',
        required=True,
    )
    # invoice_id = fields.Many2one(
    #     comodel_name='account.invoice',
    #     string='Invoice original',
    #     ondelete='cascade',
    #     required=True,
    # )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='invoice_id.sped_empresa_id',
        readonly=True,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente',
        related='invoice_id.sped_participante_id',
        readonly=True,
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal',
        related='invoice_id.sped_operacao_produto_id',
        readonly=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='invoice_id.date_invoice',
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
