# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from odoo import api, fields, models, _


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    purchase_order_id = fields.Many2one(
        string='Adicionar Pedido de Compra',
        comodel_name='purchase.order',
    )

    def _preparar_sped_documento_item(self, item):
        dados = {
            'documento_id': self.id,
            'produto_id': item.produto_id.id,
            'quantidade': item.quantidade,
            'vr_unitario': item.vr_unitario,
            'vr_frete': item.vr_frete,
            'vr_seguro': item.vr_seguro,
            'vr_desconto': item.vr_desconto,
            'vr_outras': item.vr_outras,
        }
        dados.update(item.prepara_dados_documento_item())
        return dados

    # Carregar linhas da Purchase Order
    @api.onchange('purchase_order_id')
    def purchase_order_change(self):
        if not self.purchase_order_id:
            return {}
        dados = {
            'empresa_id': self.purchase_order_id.empresa_id.id,
            'operacao_id': self.purchase_order_id.operacao_id.id,
            'modelo': self.purchase_order_id.operacao_id.modelo,
            'emissao': self.purchase_order_id.operacao_id.emissao,
            'participante_id': self.purchase_order_id.participante_id.id,
            'condicao_pagamento_id': self.purchase_order_id.condicao_pagamento_id.id if \
                self.purchase_order_id.condicao_pagamento_id else False,
            'transportadora_id': self.purchase_order_id.transportadora_id.id if \
                self.purchase_order_id.transportadora_id else False,
            'modalidade_frete': self.purchase_order_id.modalidade_frete,
        }
        dados.update(self.purchase_order_id.prepara_dados_documento())
        self.update(dados)
        self.update(self._onchange_empresa_id()['value'])
        self.update(self._onchange_operacao_id()['value'])

        if self.purchase_order_id.presenca_comprador:
            self.presenca_comprador = self.purchase_order_id.presenca_comprador

        self.update(self._onchange_serie()['value'])
        self.update(self._onchange_participante_id()['value'])

        itens = self.env['sped.documento.item']
        for item in self.purchase_order_id.order_line - \
                self.item_ids.mapped('purchase_line_id'):
            dados = self._preparar_sped_documento_item(item)
            contexto = {
                'forca_vr_unitario': dados['vr_unitario']
            }
            sped_documento_item = itens.with_context(contexto)
            documento_item = sped_documento_item.new(dados)
            itens += documento_item


        self.item_ids += itens
        return {}

    @api.onchange('participante_id', 'item_ids')
    def _onchange_allowed_purchase_ids(self):
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        purchase_line_ids = self.item_ids.mapped('purchase_line_id')
        purchase_ids = self.item_ids.mapped('purchase_id').filtered(lambda r: r.order_line <= purchase_line_ids)

        result['domain'] = {'purchase_order_id': [
            ('invoice_status', '=', 'to invoice'),
            ('participante_id', 'child_of', self.participante_id.id),
            ('id', 'not in', purchase_ids.ids),
        ]}
        return result

    @api.model
    def create(self, vals):
        documento = super(SpedDocumento, self).create(vals)
        for item in documento.item_ids:
            item.calcula_impostos()
        return documento
