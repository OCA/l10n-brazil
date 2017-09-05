# -*- coding: utf-8 -*-
#
# Copyright 2016 KMEE
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.sped_imposto.models.sped_calculo_imposto_produto_servico \
    import SpedCalculoImpostoProdutoServico
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO,
)

class AccountInvoice(SpedCalculoImpostoProdutoServico, models.Model):
    _inherit = 'account.invoice'

    #
    # O campo item_ids serve para que a classe SpedCalculoImposto
    # saiba de quais itens virão os valores que serão somados nos
    # campos totalizados de impostos, valor do produto e valor da NF e fatura
    #
    item_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='invoice_id',
        string='Itens da venda',
    )
    documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='account_invoice_id',
        string='Documentos Fiscais',
        copy=False,
    )
    quantidade_documentos = fields.Integer(
        string='Quantidade de documentos fiscais',
        compute='_compute_quantidade_documentos_fiscais',
        readonly=True,
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        related='invoice_line_ids.produto_id',
        string='Produto',
    )

    #
    # As 2 operações fiscais abaixo servem para que se calcule ao mesmo tempo,
    # numa venda ou compra, os impostos de acordo com o documento correto
    # para produtos e serviços, quando via de regra sairão 2 notas fiscais,
    # uma de produto e outra separada de serviço (pela prefeitura)
    #
    operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal (produtos)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_PRODUTO)],
    )
    operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal (serviços)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_SERVICO)],
    )

    #
    # Os 2 campos abaixo separam os itens da venda ou compra, para que se
    # informem em telas separadas os produtos dos serviços, mostrando somente
    # os campos adequados a cada caso
    #
    sale_order_line_produto_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='invoice_id',
        string='Produto',
        copy=True,
        domain=[('tipo_item','=','P')],
    )
    sale_order_line_servico_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='invoice_id',
        string='Serviços',
        copy=True,
        domain=[('tipo_item','=','S')],
    )

    #
    # Datas sem hora no fuso horário de Brasília, para relatórios e pesquisas,
    # porque data sem hora é vida ;)
    #
    data_fatura = fields.Date(
        string='Data da fatura',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    @api.depends('date')
    def _compute_data_hora_separadas(self):
        for invoice in self:
            data, hora = self._separa_data_hora(invoice.date_invoice)
            invoice.data_fatura = data
            #invoice.hora_pedido = hora

    @api.depends('documento_ids.situacao_fiscal')
    def _compute_quantidade_documentos_fiscais(self):
        for invoice in self:
            documento_ids = self.documento_ids.search(
                [('account_invoice_id', '=', invoice.id), ('situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            invoice.quantidade_documentos = len(documento_ids)

    @api.depends(
        'invoice_line_ids.price_subtotal',
        'tax_line_ids.amount',
        'currency_id',
        'company_id',
        'date_invoice',
        'type',
        #
        # Brasil
        #
        'invoice_line_ids.vr_nf',
        'invoice_line_ids.vr_fatura',
    )
    def _compute_amount(self):
        self.ensure_one()
        if not self.is_brazilian:
            return super(AccountInvoice, self)._compute_amount()

        #
        # Aqui repassamos os valores que no core são somados dos itens, mas
        # buscando da soma dos campos brasileiros;
        # amount_untaxed é o valor da operação, sem os impostos embutidos
        # amount_tax é a somas dos impostos que entraram no total da NF
        # amount_total é o saldo
        # O core não tem um campo para o nosso conceito de retenção de
        # impostos, portanto o amount_total, quando houver retenção,
        # não vai corresponder à soma do amount_untaxed + amount_tax,
        # porque não existe um campo amount_tax_retention ou
        # coisa que o valha
        #
        dados = {
            'amount_untaxed': self.vr_operacao,
            'amount_tax': self.vr_nf - self.vr_operacao,
            'amount_total': self.vr_fatura,
        }
        self.update(dados)

        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if (self.currency_id and self.company_id and
                self.currency_id != self.company_id.currency_id):
            currency_id = self.currency_id.with_context(
                date=self._get_date())
            amount_total_company_signed = \
                currency_id.compute(self.amount_total,
                                    self.company_id.currency_id)
            amount_untaxed_signed = \
                currency_id.compute(self.amount_untaxed,
                                    self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    def prepara_dados_documento(self):
        self.ensure_one()

        return {
            'account_invoice_id': self.id,
        }

    @api.onchange('empresa_id', 'participante_id')
    def _onchange_empresa_operacao_padrao(self):
        self.ensure_one()

        if not self.presenca_comprador:
            self.presenca_comprador = self.empresa_id.presenca_comprador

        if self.empresa_id.operacao_produto_id:
            self.operacao_produto_id = self.empresa_id.operacao_produto_id

        if self.participante_id and \
           self.empresa_id.operacao_produto_pessoa_fisica_id and \
            (self.participante_id.eh_consumidor_final or
             self.participante_id.tipo_pessoa == TIPO_PESSOA_FISICA):
            self.operacao_produto_id = \
                self.empresa_id.operacao_produto_pessoa_fisica_id

        if self.empresa_id.operacao_servico_id:
            self.operacao_servico_id = self.empresa_id.operacao_servico_id

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).write(dados)

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if invoice.is_brazilian:
                continue
            super(AccountInvoice, self).action_move_create()
        return True

    #@api.multi
    #def invoice_validate(self):
        #brazil = self.filtered(lambda inv: inv.is_brazilian)
        #brazil.action_sped_create()

        #not_brazil = self - brazil

        #return super(AccountInvoice, not_brazil | brazil).invoice_validate()
