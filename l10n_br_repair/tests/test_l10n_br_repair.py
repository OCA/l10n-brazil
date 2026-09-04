# Copyright 2018 Akretion - www.akretion.com.br - Magno Costa <magno.costa@akretion.com
# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class L10nBrRepairBaseTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.so_products = cls.env.ref("l10n_br_repair.main_so_only_products")
        cls.so_services = cls.env.ref("l10n_br_repair.main_so_only_services")
        cls.so_prod_srv = cls.env.ref("l10n_br_repair.main_so_product_service")
        cls.fsc_op_sale = cls.env.ref("l10n_br_fiscal.fo_venda")

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_move_ids_onchanges(self, move):
        for fn_name in (
            "_onchange_product_id_fiscal",
            "_onchange_product_uom",
            "_onchange_fiscal_operation_id",
            "_onchange_fiscal_operation_line_id",
            "_onchange_fiscal_taxes",
            "_onchange_fiscal_tax_ids",
        ):
            fn = getattr(move, fn_name, None)
            if fn:
                fn()

    def _assert_repair_fiscal_mapping(self, repair_order):
        self.assertTrue(repair_order.fiscal_operation_id)
        for move in repair_order.move_ids.filtered("is_repair_line"):
            self._run_move_ids_onchanges(move)
            self.assertTrue(move.fiscal_operation_id)
            self.assertTrue(move.fiscal_operation_line_id)

    def test_l10n_br_repair_products(self):
        self._change_user_company(self.company)
        self._assert_repair_fiscal_mapping(self.so_products)

    def test_l10n_br_repair_services(self):
        self._change_user_company(self.company)
        self._assert_repair_fiscal_mapping(self.so_services)

    def test_l10n_br_repair_products_services(self):
        self._change_user_company(self.company)
        self._assert_repair_fiscal_mapping(self.so_prod_srv)
