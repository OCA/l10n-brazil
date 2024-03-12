# Copyright (C) 2020  Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        # IMPORTANTE: a sequencia de update dos dicionarios quando o
        # partner_shipping_id é diferente, o metodo do fiscal está
        # sobre escrevendo o partner_id e acaba criando um picking
        # sem o partner_id caso esse dict atualize o do super
        values = {}
        fiscal_operation = False
        if self.sale_line_id:
            fiscal_operation = self.sale_line_id.order_id.fiscal_operation_id
            if fiscal_operation:
                values = self.sale_line_id.order_id._prepare_br_fiscal_dict()

        values.update(super()._get_new_picking_values())
        # O self pode conter mais de uma stock.move por isso a Operação Fiscal
        # usada é a do cabeçalho do Pedido de Venda já que nas linhas podem ser
        # usadas diferentes Operações Fiscais
        if fiscal_operation:
            values.update({"fiscal_operation_id": fiscal_operation.id})

        return values
