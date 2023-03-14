# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestL10nBrPosStock(TransactionCase):
    def test_create_and_do_scrap_l10n_brazil_pos(self):

        product_id = self.env['product.product'].search([], limit=1)
        scrap_vals = {
            "product_id": product_id.id,
            "product_uom_id": product_id.uom_id.id,
            "scrap_qty": 1
        }
        scrap = self.env["stock.scrap"].create_and_do_scrap(scrap_vals)

        self.assertEqual(1, len(scrap), "Error creating scrap.")
        self.assertEqual(scrap.state, 'done', "Error validating scrap")
