# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


# for some reason conversion to SavepointCase fails
class TestL10nBrPosConfig(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        self.pos_config = self.env.ref("l10n_br_pos.pos_config_presumido")

    def test_pos_config_sales_fiscal_operation(self):
        self.pos_config.out_pos_fiscal_operation_id = self.env.ref(
            "l10n_br_fiscal.fo_venda"
        )
        self.pos_config._compute_allowed_tax()
        self.assertEqual(
            4,
            len(self.pos_config.out_pos_fiscal_operation_line_ids),
            "Tax operations lines were not found.",
        )

    def test_pos_config_false_fiscal_operation(self):
        self.pos_config.out_pos_fiscal_operation_id = False
        self.pos_config._compute_allowed_tax()
        self.assertEqual(
            0,
            len(self.pos_config.out_pos_fiscal_operation_line_ids),
            "There should be no lines when the fiscal operation is false.",
        )

    def test_update_pos_config_fiscal_map(self):
        self.pos_config.update_pos_fiscal_map()
        self.assertEqual(
            36,
            len(self.pos_config.pos_fiscal_map_ids),
            "No tax data was generated for the products.",
        )
