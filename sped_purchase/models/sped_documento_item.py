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
            item.faturar_linhas()

    @api.multi
    def mesclar_linhas(self, dados, line, contexto):
        for linha in self:
            mesclar = True
            for item in dados.keys():
                if item == 'quantidade' or linha[item] == dados[item]:
                    continue
                elif isinstance(linha[item], models.Model) and \
                                linha[item].id == dados[item]:
                    continue
                else:
                    mesclar = False
            if mesclar:
                linha.quantidade += dados.get('quantidade')
                linha.purchase_line_ids += line
                linha.purchase_ids += line.order_id
                return []

        return self.with_context(contexto).new(dados)



    @api.model
    def create(self, dados):
        res = super(SpedDocumentoItem, self).create(dados)
        res.executa_depois_create()
        return res

    @api.multi
    def write(self, vals):
        res = super(SpedDocumentoItem, self).write()
        self.executa_depois_create()
        return res

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
