# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _get_fiscal_document_access_keys_fields(self):
        su = super(StockPicking, self)
        return su._get_fiscal_document_access_keys_fields() + [
            "pos_order_ids.chave_cfe"
        ]


class StockScrap(models.Model):

    _inherit = "stock.scrap"

    @api.model
    def create_and_do_scrap(self, vals):
        return self.create(vals).do_scrap()
