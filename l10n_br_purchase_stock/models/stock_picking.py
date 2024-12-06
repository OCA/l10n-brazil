# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_default_fiscal_operation(self):
        fiscal_operation = super()._get_default_fiscal_operation()
        if self.purchase_id:
            if self.purchase_id.fiscal_operation_id:
                # Evita a inconsistência de ter o Pedido de Compras com uma
                # OP Fiscal e a Ordem de Seleção outra, quando o campo
                # invoice_state é alterado, o usuário pode alterar o campo
                # mas dessa forma forçamos a decisão de não usar a mesma
                # do Pedido.
                if fiscal_operation != self.purchase_id.fiscal_operation_id:
                    fiscal_operation = self.purchase_id.fiscal_operation_id

        return fiscal_operation
