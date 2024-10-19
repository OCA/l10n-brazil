# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        # Caso tenha Sale Line já vem desagrupado aqui devido ao KEY
        if len(self) == 1:
            # Caso venha apenas uma linha porem sem
            # sale_line_id é preciso ignora-la
            if (
                self.sale_line_id
                and self.bom_line_id.bom_id.type == "phantom"
                and self.fiscal_operation_id
            ):
                result = self._get_product_price()

        return result

    def _get_new_picking_values(self):
        values = super()._get_new_picking_values()
        kit_moves = self.filtered(
            lambda move: move.sale_line_id
            and move.bom_line_id.bom_id.type == "phantom"
            and move.fiscal_operation_id
        )
        for move in kit_moves:
            move._onchange_product_id_fiscal()
            move._get_product_price()
        return values
