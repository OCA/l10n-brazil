# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class L10nBrSaleBaseTest(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.main_company = self.env.ref('base.main_company')
        self.company = self.env.ref('base.main_company')
        self.so_recurrency_service = \
            self.env.ref('l10n_br_product_contract.main_so_recurrency_service')
        self.sl_recurrency_service = \
            self.env.ref('l10n_br_product_contract.main_sl_recurrency_service_1_1')

    def test_l10n_br_product_contract_confirm_so(self):
        self.so_recurrency_service.action_confirm()
        self.assertTrue(self.sl_recurrency_service.contract_id.
                        contract_line_ids[0].fiscal_operation_id)
        self.assertTrue(self.sl_recurrency_service.contract_id.
                        contract_line_ids[0].fiscal_operation_line_id)
