# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_nfe.models.document import NFe

_logger = logging.getLogger(__name__)


class TestNFCeAccountMove(TransactionCase):
    def setUp(self):
        super().setUp()

        self.company_id = self.env.ref("base.main_company")
        self.document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        self.document_id.company_id = self.company_id

        self.setup_move_id()

    def setup_move_id(self):
        receivable_acc_id = self.env["account.account"].create(
            {
                "name": "TEST RECEIVABLE ACC",
                "code": "1.1.0.0",
                "company_id": self.company_id.id,
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        payable_acc_id = self.env["account.account"].create(
            {
                "name": "TEST PAYABLE ACC",
                "code": "1.1.0.2",
                "company_id": self.company_id.id,
                "user_type_id": self.env.ref("account.data_account_type_payable").id,
                "reconcile": True,
            }
        )
        journal_id = self.env["account.journal"].create(
            {
                "name": "Journal TESTE",
                "code": "TESTJOURNAL",
                "company_id": self.company_id.id,
                "type": "sale",
            }
        )
        product_id = self.env["product.product"].create(
            {"name": "PRODUCT TEST", "default_code": "TEST11", "lst_price": 10}
        )
        self.move_id = self.env["account.move"].create(
            {
                "name": "MOVE INVOICE TEST",
                "move_type": "out_invoice",
                "journal_id": journal_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": payable_acc_id.id,
                            "debit": 10,
                            "product_id": product_id.id,
                            "quantity": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": receivable_acc_id.id,
                            "credit": 10,
                            "product_id": product_id.id,
                            "quantity": 1,
                        },
                    ),
                ],
                "document_type_id": self.env.ref("l10n_br_fiscal.document_65").id,
                "fiscal_operation_id": self.document_id.fiscal_operation_id.id,
                "fiscal_document_id": self.document_id.id,
                "document_date": datetime.now(),
            }
        )

    @mock.patch.object(NFe, "get_nfce_qrcode", return_value=None)
    @mock.patch.object(NFe, "get_nfce_qrcode_url", return_value=None)
    def test_view_pdf(self, mock_qrcode, mock_qrcode_url):
        action_pdf = self.move_id.view_pdf()
        report_action = action_pdf["context"]["report_action"]

        self.assertEqual(report_action["report_file"], "l10n_br_pos_nfce.danfe_nfce")
        self.assertEqual(
            report_action["report_name"], "l10n_br_pos_nfce.report_danfe_nfce"
        )
        self.assertEqual(report_action["report_type"], "qweb-html")

        self.move_id.document_type = "55"
        with self.assertRaises(UserError):
            self.move_id.view_pdf()

    def test_prepare_nfce_values_for_pdf(self):
        line_values = self.move_id._prepare_nfce_danfe_line_values()

        line1 = line_values[0]
        self.assertEqual(line1["product_name"], "PRODUCT TEST")
        self.assertEqual(line1["product_quantity"], 1)
        self.assertEqual(line1["product_unit_value"], 10)
        self.assertEqual(line1["product_unit_total"], 10)

        detpag = [
            (
                0,
                0,
                {
                    "nfe40_indPag": "1",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": 10,
                },
            )
        ]
        self.move_id.fiscal_document_id.nfe40_detPag = detpag

        payment_values = self.move_id._prepare_nfce_danfe_payment_values()
        payment = payment_values[-1]

        self.assertEqual(payment["method"], "01 - Dinheiro")
        self.assertEqual(payment["value"], 10)
