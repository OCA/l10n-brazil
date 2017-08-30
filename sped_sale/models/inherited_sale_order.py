# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto_produto_servico \
    import SpedCalculoImpostoProdutoServico
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO,
)


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

    #
    # As 2 operações fiscais abaixo servem para que se calcule ao mesmo tempo,
    # numa venda ou compra, os impostos de acordo com o documento correto
    # para produtos e serviços, quando via de regra sairão 2 notas fiscais,
    # uma de produto e outra separada de serviço (pela prefeitura)
    #
    sped_operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal (produtos)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_PRODUTO)],
    )
    sped_operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação Fiscal (serviços)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_SERVICO)],
    )

    sale_order_line_produto_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='order_id',
        string='Produto',
        copy=True,
        domain=[('tipo_item','=','P')],
    )

    sale_order_line_servico_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='order_id',
        string='Serviços',
        copy=True,
        domain=[('tipo_item','=','S')],
    )

    sped_documento_ids = fields.One2many(
        comodel_name='sped.documento',
        inverse_name='sale_order_id',
        string='Documentos Fiscais',
        copy=False,
    )

    data_pedido = fields.Date(
        string='Data do pedido',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )

    @api.depends('date_order')
    def _compute_data_hora_separadas(self):
        for sale in self:
            data, hora = self._separa_data_hora(sale.date_order)
            sale.data_pedido = data
            #sale.hora_pedido = hora

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

        vals['sped_empresa_id'] = self.empresa_id.id or False
        vals['sped_participante_id'] = self.participante_id.id or False
        vals['sped_operacao_produto_id'] = \
            self.sped_operacao_produto_id.id or False
        vals['sped_operacao_servico_id'] = \
            self.sped_operacao_servico_id.id or False
        vals['condicao_pagamento_id'] = \
            self.condicao_pagamento_id.id or False
        vals['date_invoice'] = fields.Date.context_today(self)

        return vals

    @api.depends('state', 'order_line.invoice_status',
                 'sped_documento_ids.situacao_fiscal')
    def _get_invoiced(self):
        for sale in self:
            super(SaleOrder, sale)._get_invoiced()

            if not sale.is_brazilian:
                continue

            sped_documento_ids = self.sped_documento_ids.search(
                [('sale_order_id', '=', sale.id), ('situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            invoice_count = len(sped_documento_ids)

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

    @api.multi
    def action_view_sped_documento(self):
        action = self.env.ref('sped.sped_documento_emissao_nfe_acao').read()[0]

        if len(self.sped_documento_ids) > 1:
            action['domain'] = [('id', 'in', self.sped_documento_ids.ids)]

        elif len(self.sped_documento_ids) == 1:
            action['views'] = [
                (self.env.ref('sped.sped_documento_emissao_nfe_form').id,
                 'form')]
            action['res_id'] = self.sped_documento_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action


    def prepara_dados_sped_documento(self):
        self.ensure_one()

        return {
            'sale_order_id': self.id,
        }
