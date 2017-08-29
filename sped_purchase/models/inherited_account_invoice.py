# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('purchase_id')
    def _purchase_order_change_brazil(self):
        self.sped_participante_id = self.purchase_id.sped_participante_id
        self.sped_operacao_produto_id = \
            self.purchase_id.sped_operacao_produto_id
        self.sped_operacao_servico_id = \
            self.purchase_id.sped_operacao_servico_id
        self.condicao_pagamento_id = self.purchase_id.condicao_pagamento_id

    @api.multi
    def _prepare_invoice_line_from_po_line(self, line):
        # TODO: Refatorar isto para que o purchase e o sale chamem a mesma
        # função
        res = super(
            AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if self.is_brazilian:
            res['produto_id'] = line.produto_id.id
            res['quantidade'] = line.quantidade
            res['vr_unitario'] = line.vr_unitario
            res['vr_desconto'] = line.vr_desconto
            res['unidade_id'] = line.unidade_id.id
            res['protocolo_id'] = line.protocolo_id.id
            res['operacao_item_id'] = line.operacao_item_id.id
            res['unidade_id'] = line.unidade_id.id
            res['vr_seguro'] = line.vr_seguro
            res['vr_outras'] = line.vr_outras
            res['vr_frete'] = line.vr_frete
        return res
