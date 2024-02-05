# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest import mock

import odoo

from odoo.addons.l10n_br_fiscal.models.document_workflow import DocumentWorkflow
from odoo.addons.l10n_br_nfe.models.document import NFe

from .common import TestNFCePosOrderCommon


@odoo.tests.tagged("post_install", "-at_install")
class TestNFCePosOrder(TestNFCePosOrderCommon):
    def test_nfce_order_creation(self):
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.env.user.company_ids = [(4, self.company.id)]
        self.env.user.company_id = self.company

        self.open_new_session()

        self.customer.is_anonymous_consumer = True
        order_data = self.create_ui_order_data(
            [(self.product1, 5)], payments=[(self.cash_pm, 50)], customer=self.customer
        )

        ctg_order_data = order_data
        ctg_order_data["data"]["authorization_protocol"] = False
        ctg_order_data["data"]["document_key"] = "dummy"
        ctg_order_data["data"]["document_number"] = 1000
        ctg_order_data["data"]["company_id"] = self.env.user.company_id.id
        ctg_order_data["data"]["to_invoice"] = True

        res = self.env["pos.order"].create_from_ui([ctg_order_data])
        contingency_order = self.env["pos.order"].browse(res[0].get("id"))

        self.assertTrue(contingency_order.is_contingency)
        self.assertEqual(contingency_order.document_number, "1000")
        self.assertEqual(contingency_order.document_key, "dummy")
        self.assertEqual(self.config.nfce_document_serie_sequence_number_next, 1000)

        order_data["data"]["to_invoice"] = True
        order_data["data"]["authorization_protocol"] = "dummy"
        order_data["data"]["cnpj_cpf"] = "44300963000186"
        res = self.env["pos.order"].create_from_ui([order_data])
        cnpj_order = self.env["pos.order"].browse(res[0].get("id"))

        self.assertFalse(cnpj_order.partner_id.cnpj_cpf)
        self.assertEqual(cnpj_order.document_number, "1000")
        self.assertEqual(self.config.nfce_document_serie_sequence_number_next, 1001)

        order_data["data"]["cnpj_cpf"] = "42820627030"

        with mock.patch.object(DocumentWorkflow, "action_document_confirm"):
            # nothing will happen
            res = self.env["pos.order"].create_from_ui([order_data])

        cpf_order = self.env["pos.order"].browse(res[0].get("id"))
        self.assertFalse(cpf_order.partner_id.cnpj_cpf)

        cpf_order.payment_ids = False
        vals = cpf_order._prepare_nfce_vals("dummy")
        self.assertEqual(vals, dict())

        document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        cpf_order.account_move.fiscal_document_id = document_id
        cpf_order.account_move.fiscal_document_id.authorization_date = datetime.now()

        with mock.patch.object(
            NFe, "get_nfce_qrcode", return_value=None
        ), mock.patch.object(NFe, "get_nfce_qrcode_url", return_value=None):
            doc_dict = cpf_order._prepare_fiscal_document_dict()
            self.assertEqual(
                doc_dict["document_key"], "33230807984267003800650040000000321935136447"
            )

    def test_cancel_nfce_from_ui(self):
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.env.user.company_ids = [(4, self.company.id)]
        self.env.user.company_id = self.company

        self.open_new_session()

        order_data = self.create_ui_order_data(
            [(self.product1, 5)], payments=[(self.cash_pm, 50)], customer=self.customer
        )
        order_data["data"]["to_invoice"] = True
        res = self.env["pos.order"].create_from_ui([order_data])
        order_id = self.env["pos.order"].browse(res[0].get("id"))

        self.env["pos.order"].cancel_nfce_from_ui(order_id.pos_reference, "Teste")

        refund_order = self.env["pos.order"].search(
            [
                ("pos_reference", "=", order_id.pos_reference),
                ("amount_total", ">", 0),
            ],
            limit=1,
        )
        self.assertIn("cancelled", refund_order.pos_reference)

    def test_pos_config_next_nfce_number(self):
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.env.user.company_ids = [(4, self.company.id)]
        self.env.user.company_id = self.company

        def_next_number = self.config._default_next_number()
        self.assertEqual(def_next_number, 1)

        serie_id = self.env.ref("l10n_br_pos_nfce.document_65_serie_2")
        serie_id.internal_sequence_id = self.env["ir.sequence"].create(
            {
                "name": "NFCe SERIE",
                "code": "l10n_br_fiscal.document.serie",
                "prefix": "SERIE",
            }
        )
        self.config.nfce_document_serie_id = serie_id
        def_next_number = self.config._default_next_number()

        self.assertEqual(
            def_next_number, serie_id.internal_sequence_id.number_next_actual
        )

        new_number = self.config.update_nfce_serie_number(2000)
        self.assertEqual(new_number, 2000)

        new_number = self.config.update_nfce_serie_number(500)
        self.assertEqual(new_number, 2000)
