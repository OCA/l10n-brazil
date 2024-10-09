# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        # Caso tenha Purchase Line já vem desagrupado aqui devido ao KEY
        if len(self) == 1:
            # Caso venha apenas uma linha porem sem
            # purchase_line_id é preciso ignora-la
            if self.purchase_line_id and self.purchase_line_id.price_unit != result:
                result = self.purchase_line_id.price_unit

        return result
