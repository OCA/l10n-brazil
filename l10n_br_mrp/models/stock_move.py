# Copyright (C) 2023-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _simulate_fiscal_onchange(self, values, bom_line, quantity):
        values.update({
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
        })
        move = self.env['stock.move'].new(values.copy())
        move._onchange_product_id_fiscal()
        new_values = move._convert_to_write(move._cache)
        values.update(new_values)
        return values

    def _prepare_phantom_move_values(self, bom_line, quantity):
        values = super()._prepare_phantom_move_values(bom_line, quantity)
        values = self._simulate_fiscal_onchange(values, bom_line, quantity)
        return values
