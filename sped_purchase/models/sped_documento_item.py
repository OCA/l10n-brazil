# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    purchase_line_ids = fields.Many2many(
        string='Linha do pedido',
        comodel_name='purchase.order.line',
        copy=False,
    )

    purchase_ids = fields.Many2many(
        string='Pedido de compra',
        comodel_name='purchase.order',
        copy=False,
    )

    pode_alterar_quantidade = fields.Boolean(
        string='Pode alterar a quantidade?',
        default=True,
    )

    def faturar_linhas(self):
        for linha in self.mapped('purchase_line_ids'):
            total = 0.0
            for qty in linha.documento_item_ids.mapped('quantidade'):
                total += qty
            linha.qty_invoiced = total

    def executa_depois_create(self):
        for item in self:
            data = {
                'produto_id': item.produto_id,
                'quantidade': item.quantidade,
                'vr_unitario': item.vr_unitario,
                'vr_frete': item.vr_frete,
                'vr_seguro': item.vr_seguro,
                'vr_desconto': item.vr_desconto,
                'vr_outras': item.vr_outras,
            }
            for linha in item.purchase_ids.mapped('order_line') - \
                    item.mapped('purchase_line_ids'):
                if all(linha[field] == data[field] for field in data.keys()):
                    item.purchase_line_ids += linha

    @api.onchange('purchase_ids', 'purchase_line_ids')
    def _onchange_purchase_line_ids(self):
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        purchase_line_ids = self.purchase_ids.mapped('order_line')

        result['domain'] = {'purchase_line_ids': [
            ('id', 'in', purchase_line_ids.ids),
            ('id', 'not in', self.purchase_line_ids.ids),
        ], 'purchase_ids': [
            ('invoice_status', '=', 'to invoice'),
            ('id', 'not in', self.purchase_ids.ids),
        ]}

        if self.participante_id:
            result['domain']['purchase_line_ids'].append(
                ('participante_id', '=', self.participante_id.id)
            )
            result['domain']['purchase_ids'].append(
                ('participante_id', '=', self.participante_id.id)
            )

        if self.empresa_id:
            result['domain']['purchase_line_ids'].append(
                ('empresa_id', '=', self.empresa_id.id)
            )
            result['domain']['purchase_ids'].append(
                ('empresa_id', '=', self.empresa_id.id)
            )

        if self.produto_id:
            result['domain']['purchase_line_ids'].append(
                ('produto_id', '=', self.produto_id.id)
            )

        if self.vr_unitario:
            result['domain']['purchase_line_ids'].append(
                ('vr_unitario', '=', self.vr_unitario)
            )

        if len(self.purchase_line_ids) > 1:
            self.pode_alterar_quantidade = False
            quantidade = 0
            for linha in self.purchase_line_ids:
                quantidade += linha.quantidade
            self.quantidade = quantidade
        else:
            self.pode_alterar_quantidade = True

        return result

    @api.onchange('quantidade')
    def constrains_quantidade(self):
        for item in self:
            if item.purchase_line_ids and len(item.purchase_line_ids) == 1:
                disponivel = item.purchase_line_ids.quantidade - \
                             item.purchase_line_ids.qty_invoiced
                if not (item.quantidade > disponivel):
                    raise ValidationError(_(
                        'Quantidade do item ' + item.produto_id.nome +
                        'ultrapassa o disponível na linha do pedido de compra.'
                    ))
