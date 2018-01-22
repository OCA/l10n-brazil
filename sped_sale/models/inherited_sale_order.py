# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto_produto_servico \
    import SpedCalculoImpostoProdutoServico
from odoo.addons.l10n_br_base.constante_tributaria import *


class SaleOrder(SpedCalculoImpostoProdutoServico, models.Model):
    _inherit = 'sale.order'

    #
    # O campo item_ids serve para que a classe SpedCalculoImposto
    # saiba de quais itens virão os valores que serão somados nos
    # campos totalizados de impostos, valor do produto e valor da NF e fatura
    #
    item_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='order_id',
        string='Itens da venda',
    )
    documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='sale_order_id',
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
        related='order_line.produto_id',
        string='Produto',
    )

    #
    # Os 2 campos abaixo separam os itens da venda ou compra, para que se
    # informem em telas separadas os produtos dos serviços, mostrando somente
    # os campos adequados a cada caso
    #
    sale_order_line_produto_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='order_id',
        string='Produto',
        copy=False,
        domain=[('tipo_item','=','P')],
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    sale_order_line_servico_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='order_id',
        string='Serviços',
        copy=False,
        domain=[('tipo_item','=','S')],
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    #
    # Datas sem hora no fuso horário de Brasília, para relatórios e pesquisas,
    # porque data sem hora é vida ;)
    #
    data_pedido = fields.Date(
        string='Data do pedido',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    #
    # Corrige os states
    #
    state = fields.Selection(
        selection=[
            ('draft', 'Orçamento'),
            ('sent', 'Enviado ao cliente'),
            ('sale', 'Pedido'),
            ('done', 'Concluído'),
            ('cancel', 'Cancelado'),
        ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft',
    )

    obs_estoque = fields.Text(
        string='Obs. para o estoque',
    )

    @api.depends('date_order')
    def _compute_data_hora_separadas(self):
        for sale in self:
            data, hora = self._separa_data_hora(sale.date_order)
            sale.data_pedido = data
            #sale.hora_pedido = hora

    @api.depends('documento_ids.situacao_fiscal')
    def _compute_quantidade_documentos_fiscais(self):
        for sale in self:
            documento_ids = self.env['sped.documento'].search(
                [('sale_order_id', '=', sale.id)])

            sale.quantidade_documentos = len(documento_ids)

    @api.depends(
        'order_line.price_total',
        #
        # Brasil
        #
        'order_line.vr_nf',
        'order_line.vr_fatura',
    )
    def _amount_all(self):
        for sale in self:
            if not sale.is_brazilian:
                super(SaleOrder, sale)._amount_all()

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
                'amount_untaxed': sale.vr_operacao,
                'amount_tax': sale.vr_nf - sale.vr_operacao,
                'amount_total': sale.vr_fatura,
            }
            sale.update(dados)

    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()

        vals['empresa_id'] = self.empresa_id.id or False
        vals['participante_id'] = self.participante_id.id or False
        vals['operacao_produto_id'] = \
            self.operacao_produto_id.id or False
        vals['operacao_servico_id'] = \
            self.operacao_servico_id.id or False
        vals['condicao_pagamento_id'] = \
            self.condicao_pagamento_id.id or False
        vals['date_invoice'] = fields.Date.context_today(self)

        return vals

    @api.depends('state', 'order_line.invoice_status',
                 'documento_ids.situacao_fiscal')
    def _get_invoiced(self):
        for sale in self:
            super(SaleOrder, sale)._get_invoiced()

            if not sale.is_brazilian:
                continue

            documento_ids = self.env['sped.documento'].search(
                [('sale_order_id', '=', sale.id), ('situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            invoice_count = len(documento_ids)

            line_invoice_status = [line.invoice_status for line in
                                   sale.order_line]

            if sale.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' \
                for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' \
                for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] \
                for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'

            sale.update({
                'invoice_count': invoice_count,
                'invoice_status': invoice_status
            })

    def prepara_dados_documento(self):
        self.ensure_one()

        return {
            'sale_order_id': self.id,
            'infcomplementar': self.note,
        }

    @api.onchange('empresa_id', 'participante_id')
    def _onchange_empresa_operacao_padrao(self):
        self.ensure_one()

        if not self.presenca_comprador:
            self.presenca_comprador = self.empresa_id.presenca_comprador

        if self.empresa_id.operacao_produto_id:
            self.operacao_produto_id = self.empresa_id.operacao_produto_id

        if self.participante_id:
            if self.empresa_id.operacao_produto_pessoa_fisica_id and \
                (self.participante_id.eh_consumidor_final or
                 self.participante_id.tipo_pessoa == TIPO_PESSOA_FISICA):
                self.operacao_produto_id = \
                 self.empresa_id.operacao_produto_pessoa_fisica_id
            if self.participante_id.comment:
                self.obs_estoque = self.participante_id.comment

        if self.empresa_id.operacao_servico_id:
            self.operacao_servico_id = self.empresa_id.operacao_servico_id

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).write(dados)

    def gera_documento(self, soh_produtos=False, soh_servicos=False,
                       stock_picking=None):
        self.ensure_one()

        documento_produto, documento_servico = \
            super(SaleOrder, self).gera_documento(
                soh_produtos=soh_produtos, soh_servicos=soh_servicos
            )

        if documento_produto is not None:
            #
            # Setamos a transportadora e a modalidade
            #
            if self.modalidade_frete:
                documento_produto.modalidade_frete = self.modalidade_frete

            if self.transportadora_id:
                documento_produto.transportadora_id = self.transportadora_id.id

            if stock_picking is None:
                if documento_produto.operacao_id.enviar_pela_venda:
                    documento_produto.envia_documento()

        #if documento_servico is not None:
            #if documento_servico.operacao_id.enviar_pela_venda:
                #documento_servico.envia_nfse()

        return documento_produto, documento_servico
