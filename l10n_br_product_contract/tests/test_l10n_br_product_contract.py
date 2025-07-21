# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class L10nBrSaleBaseTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.main_company = cls.env.ref("base.main_company")
        cls.company = cls.env.ref("base.main_company")
        cls.so_recurrency_service = cls.env.ref(
            "l10n_br_product_contract.main_so_recurrency_service"
        )
        cls.sl_recurrency_service = cls.env.ref(
            "l10n_br_product_contract.main_sl_recurrency_service_1_1"
        )

    def test_l10n_br_product_contract_confirm_so(self):
        self.so_recurrency_service.action_confirm()
        self.assertTrue(
            self.sl_recurrency_service.contract_id.contract_line_ids[
                0
            ].fiscal_operation_id
        )
        self.assertTrue(
            self.sl_recurrency_service.contract_id.contract_line_ids[
                0
            ].fiscal_operation_line_id
        )
