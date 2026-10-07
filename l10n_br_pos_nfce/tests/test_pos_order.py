# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest import mock

import odoo

from odoo.addons.l10n_br_fiscal.models.document import Document
from odoo.addons.l10n_br_nfe.models.document import NFe

from .common import TestNFCePosOrderCommon


@odoo.tests.tagged("post_install", "-at_install")
class TestNFCePosOrder(TestNFCePosOrderCommon):
    valid_nfce_key = "33230807984267003800650040000000321935136447"

    def _prepare_order_data(self, cnpj_cpf=None):
        order_data = self.create_ui_order_data(
            [(self.product1, 5)],
            payments=[(self.cash_pm, 50)],
            customer=self.customer,
        )

        order_data["data"].update(
            {
                "to_invoice": True,
                "company_id": self.env.user.company_id.id,
            }
        )

        if cnpj_cpf:
            order_data["data"]["cnpj_cpf"] = cnpj_cpf

        return order_data

    def test_nfce_order_creation(self):
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.env.user.company_ids = [(4, self.company.id)]
        self.env.user.company_id = self.company

        self.open_new_session()
        self.customer.is_anonymous_consumer = True

        # NFC-e em contingência.
        contingency_order_data = self._prepare_order_data()
        contingency_order_data["data"].update(
            {
                "authorization_protocol": False,
                "document_key": self.valid_nfce_key,
                "document_number": 1000,
            }
        )

        result = self.env["pos.order"].create_from_ui([contingency_order_data])
        contingency_order = self.env["pos.order"].browse(result[0]["id"])
        contingency_document = contingency_order.account_move.fiscal_document_id

        self.assertTrue(contingency_order.is_contingency)
        self.assertEqual(
            contingency_document.document_number,
            "1000",
        )
        self.assertEqual(
            contingency_document.document_key,
            self.valid_nfce_key,
        )

        # NFC-e autorizada com CNPJ.
        cnpj_order_data = self._prepare_order_data(
            cnpj_cpf="44300963000186",
        )
        cnpj_order_data["data"]["authorization_protocol"] = "123456789012345"

        result = self.env["pos.order"].create_from_ui([cnpj_order_data])
        cnpj_order = self.env["pos.order"].browse(result[0]["id"])
        cnpj_document = cnpj_order.account_move.fiscal_document_id

        self.assertFalse(cnpj_order.partner_id.cnpj_cpf)
        self.assertEqual(
            cnpj_document.document_number,
            "1001",
        )

        # NFC-e autorizada com CPF.
        cpf_order_data = self._prepare_order_data(
            cnpj_cpf="42820627030",
        )
        cpf_order_data["data"]["authorization_protocol"] = "123456789012345"

        with mock.patch.object(
            Document,
            "action_document_confirm",
        ):
            result = self.env["pos.order"].create_from_ui([cpf_order_data])

        cpf_order = self.env["pos.order"].browse(result[0]["id"])
        cpf_document = cpf_order.account_move.fiscal_document_id

        self.assertFalse(cpf_order.partner_id.cnpj_cpf)

        cpf_order.payment_ids = False
        self.assertEqual(
            cpf_order._prepare_nfce_vals(self.config),
            {},
        )

        cpf_document.write(
            {
                "authorization_date": datetime.now(),
            }
        )

        with mock.patch.object(
            NFe,
            "get_nfce_qrcode",
            return_value=None,
        ), mock.patch.object(
            NFe,
            "get_nfce_qrcode_url",
            return_value=None,
        ):
            document_values = cpf_order._prepare_fiscal_document_dict()

        self.assertEqual(
            document_values["document_key"],
            cpf_document.document_key,
        )

    def test_cancel_nfce_from_ui(self):
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.env.user.company_ids = [(4, self.company.id)]
        self.env.user.company_id = self.company

        self.open_new_session()

        order_data = self._prepare_order_data()
        order_data["data"]["authorization_protocol"] = "123456789012345"

        result = self.env["pos.order"].create_from_ui([order_data])
        order = self.env["pos.order"].browse(result[0]["id"])

        self.env["pos.order"].cancel_nfce_from_ui(
            order.pos_reference,
            "Teste",
        )

        refund_order = self.env["pos.order"].search(
            [
                (
                    "pos_reference",
                    "=",
                    f"{order.pos_reference}-cancelled",
                ),
                ("id", "!=", order.id),
            ],
            limit=1,
        )

        self.assertTrue(
            refund_order,
            "The NFC-e refund order was not created",
        )
        self.assertEqual(
            refund_order.pos_reference,
            f"{order.pos_reference}-cancelled",
        )
