# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_fiscal_partner(self):
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        partner_to_invoice = self._get_partner_to_invoice()
        if partner.id != partner_to_invoice:
            partner = self.env["res.partner"].browse(partner_to_invoice)
        return partner

    def _get_default_fiscal_operation(self):
        fiscal_operation = super()._get_default_fiscal_operation()
        if self.sale_id:
            if self.sale_id.fiscal_operation_id:
                # Evita a inconsistência de ter o Pedido de Vendas com uma
                # OP Fiscal e a Ordem de Seleção outra, quando o campo
                # invoice_state é alterado, o usuário pode alterar o campo
                # mas dessa forma forçamos a decisão de não usar a mesma
                # do Pedido.
                if fiscal_operation != self.sale_id.fiscal_operation_id:
                    fiscal_operation = self.sale_id.fiscal_operation_id

        return fiscal_operation
