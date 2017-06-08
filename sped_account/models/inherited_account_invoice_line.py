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
    ENTRADA_SAIDA_SAIDA,
)
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import (
    SpedCalculoImpostoItem
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends(
        'price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        'invoice_id.company_id', 'invoice_id.date_invoice',
        #
        # Campos brasileiros
        #
        'brazil_line_id.produto_id',
        'brazil_line_id.quantidade',
        'brazil_line_id.vr_unitario',
        'brazil_line_id.vr_desconto',
        'brazil_line_id.unidade',
        # 'brazil_line_id.operacao_id',
        'brazil_line_id.operacao_item_id',
        'brazil_line_id.protocolo_id',
        # TODO: Outros campos que precisamos monitorar
    )
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        if self.is_brazilian:
            self.brazil_line_id._amount_price_brazil()

    brazil_line_id = fields.One2many(
        comodel_name='account.invoice.line.brazil',
        inverse_name='invoice_line_id',
        string='Linha da Fatura',
    )
    order_id = fields.Many2one(
        #
        # Workarround para o cálculo globalizado. Devido a diferença dos
        # modelos da invoice/sale/purchase
        #
        comodel_name='account.invoice',
        related='invoice_id',
        readonly=True,
        index=True,
    )
    sped_documento_item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string=u'Item do Documento Fiscal',
        ondelete='cascade',
    )
    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Invoice?',
        related='invoice_id.is_brazilian',
    )

    @api.multi
    def _create_brazil(self):
        Brazil = self.env["account.invoice.line.brazil"]
        for item in self:
            related_vals = {
                'invoice_line_id': item.id,
                'vr_unitario': item.price_unit,
                'quantidade': item.quantity,
                'produto_id': item.product_id.sped_produto_id.id,
                'unidade_id': item.uom_id.sped_unidade_id.id
            }
            new = Brazil.create(related_vals)
        return True

    @api.model
    def create(self, vals):
        line = super(AccountInvoiceLine, self).create(vals)
        #
        # Não podemos verificar se empresa é brasileira aqui, pois muitas
        # vezes não temos o company_id
        #
        if "create_brazil" not in self._context:
            line._create_brazil()
        return line

    @api.multi
    def _new_brazil(self):
        Brazil = self.env["account.invoice.line.brazil"]
        for item in self:
            related_vals = {
                'invoice_line_id': item.id,
                'vr_unitario': item.price_unit,
                'quantidade': item.quantity,
                'produto_id': item.product_id.sped_produto_id.id,
                'unidade_id': item.uom_id.sped_unidade_id.id
            }
            new = Brazil.new(related_vals)
        return True

    @api.model
    def new(self, values={}):
        record = super(AccountInvoiceLine, self).new(values)
        if "create_brazil" not in self._context:
            record._new_brazil()
        return record


class AccountInvoiceLineBrazil(SpedCalculoImpostoItem, models.Model):
    _name = b'account.invoice.line.brazil'
    _description = 'Linhas da Fatura'
    _inherits = {'account.invoice.line': 'invoice_line_id'}
    _abstract = False

    vr_nf = fields.Monetary(
        compute='_amount_price_brazil'
    )
    vr_fatura = fields.Monetary(
        compute='_amount_price_brazil'
    )

    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Invoice Line original',
        ondelete='restrict',
        required=True,
    )
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

    @api.model
    def create(self, vals):
        record = super(AccountInvoiceLineBrazil, self.with_context(
            create_brazil=True)).create(vals)
        record.calcula_impostos()
        return record

    # @api.model
    # Funçao usada nas criação das compras através do purchase.
    # Mas ela quebra a invoice normal.
    # def new(self, values={}):
    #     record = super(AccountInvoiceLineBrazil, self.with_context(
    #         create_brazil=True)).new(values)
    #     record.calcula_impostos()
    #     return record

    def get_invoice_line_account(self):
        if self.operacao_id.entrada_saida == ENTRADA_SAIDA_SAIDA:
            return self.product_id.property_account_income_id
        else:
            return self.product_id.property_account_expense_id

    @api.onchange('produto_id')
    def onchange_product_id_date(self):
        domain = {}
        if not self.invoice_id:
            return
        if not (self.invoice_id.sped_operacao_produto_id or
                self.invoice_id.sped_operacao_servico_id):
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'Por favor defina a operação'),
            }
            return {'warning': warning}
        account = self.get_invoice_line_account()

        if account:
            self.account_id = account.id
        if self.produto_id:
            self.name = self.produto_id.nome

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
