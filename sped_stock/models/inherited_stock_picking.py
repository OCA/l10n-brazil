# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)
from odoo.addons.l10n_br_base.constante_tributaria import (ENTRADA_SAIDA)


class SpedStockPicking(SpedCalculoImposto, models.Model):
    _inherit = 'stock.picking'

    entrada_saida = fields.Selection(
        selection=ENTRADA_SAIDA,
        related='operacao_id.entrada_saida'
    )
    documento_fiscal_criado = fields.Boolean(
        copy=False
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal Relacionado'
    )

    @api.onchange('picking_type_id')
    def _onchange_stock_picking_type(self):
        for record in self:
            if record.picking_type_id:
                record.sped_operacao_produto_id = \
                    record.picking_type_id.operacao_id.id

    def _criar_documento_itens(self, move_lines, documento):
        itens_ids = []
        for item in move_lines:
            doc_item = self.env['sped.documento.item'].create(
                item._prepare_sped_line(documento))
            # Mantemos relacionamento de ida e volta entre
            # documento_item e stock_move
            item.documento_item_id = doc_item
            itens_ids.append(doc_item.id)
        return itens_ids

    @api.multi
    def action_criar_sped_documento(self):
        documentos_criados = []
        for record in self:
            vals = record._prepare_sped(record.sped_operacao_produto_id)
            documento = self.env['sped.documento'].create(vals)

            itens_ids = self._criar_documento_itens(self.move_lines, documento)
            documento.item_ids = itens_ids

            for item in documento.item_ids:
                item.calcula_impostos()

            documentos_criados.append(documento.id)
            if documento.id:
                documento.stock_picking_id = record
                record.documento_fiscal_criado = True
                record.documento_id = documento

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Documento Gerado',
            'res_model': 'sped.documento',
            'domain': [('id', 'in', documentos_criados)],
            'view_mode': 'tree,form',
        }
        return action
