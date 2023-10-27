# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _get_fiscal_document_access_keys_fields(self):
        su = super()
        return su._get_fiscal_document_access_keys_fields() + ["pos_order_ids.key_cfe"]
