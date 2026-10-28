# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestL10nBrPosProduct(TransactionCase):
    def setUp(self):
        super().setUp()
        self.pos_config = self.env.ref("point_of_sale.pos_config_main")
        self.pos_config.partner_id = self.env.ref("l10n_br_fiscal.res_partner_anonimo")

    def test_fiscal_map_after_create_product(self):
        self.env["product.template"].create(
            {
                "name": "Product Fiscal Map",
                "type": "product",
                "fiscal_type": 00,
                "icms_origin": 0,
                "ncm_id": self.env.ref("l10n_br_fiscal.ncm_94033000").id,
                "fiscal_genre_id": self.env.ref("l10n_br_fiscal.product_genre_94").id,
                "available_in_pos": True,
            }
        )

        product = self.env["product.template"].search(
            [("name", "=", "Product Fiscal Map")]
        )

        self.assertEqual(
            1,
            len(product.pos_fiscal_map_ids),
            "Error generating POS tax information for the product created.",
        )

        product_product = self.env["product.product"].search(
            [("product_tmpl_id", "=", product.id)]
        )

        product_product.update_pos_fiscal_map()
        self.assertEqual(
            1,
            len(product.pos_fiscal_map_ids),
            "Error generating POS tax information for the product variant.",
        )
