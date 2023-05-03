# Copyright (C) 2018 - Magno Costa - Akretion
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo import fields
from odoo.models import NewId
from odoo.tests import SavepointCase


class TestSupplierInvoice(SavepointCase):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with supplier invoices.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Purchase - (test)",
                user_type_id=cls.env.ref("account.data_account_type_revenue").id,
            )
        )

        cls.purchase_journal = cls.env["account.journal"].create(
            dict(
                name="Purchase Journal - (test)",
                code="TPJ",
                type="purchase",
                refund_sequence=True,
                default_account_id=cls.purchase_account.id,
            )
        )

        cls.init_number_of_fiscal_docs = cls.env[
            "l10n_br_fiscal.document"
        ].search_count([])
        cls.init_number_of_fiscal_doc_lines = cls.env[
            "l10n_br_fiscal.document.line"
        ].search_count([])
        cls.invoice_1 = cls.env["account.move"].create(
            dict(
                name="Test Supplier Invoice 1",
                move_type="in_invoice",
                invoice_date=fields.Date.today(),
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.purchase_journal.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_5").id,
                            "quantity": 10.0,
                            "price_unit": 450.0,
                            "account_id": cls.env["account.account"]
                            .search(
                                [
                                    (
                                        "user_type_id",
                                        "=",
                                        cls.env.ref(
                                            "account.data_account_type_revenue"
                                        ).id,
                                    ),
                                    (
                                        "company_id",
                                        "=",
                                        cls.env.company.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "product test 5",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            )
        )

    def test_dummy_doc_usage(self):
        self.assertEqual(
            self.init_number_of_fiscal_docs,
            self.env["l10n_br_fiscal.document"].search_count([]),
            "Non fiscal invoices should not create fiscal documents"
            "They should use the company dummy document instead.",
        )

    def test_dummy_doc_line_usage(self):
        self.assertEqual(
            self.init_number_of_fiscal_doc_lines,
            self.env["l10n_br_fiscal.document.line"].search_count([]),
            "Non fiscal invoices should not create fiscal document lines"
            "They should use the company dummy document line instead.",
        )

    def test_create_dont_recompute_existing_moves(self):
        with mock.patch.object(
            self.env.__class__, "add_to_compute", wraps=None
        ) as mocked_env:
            invoice = self.env["account.move"].create(
                dict(
                    name="Test Supplier Invoice 1",
                    move_type="in_invoice",
                    invoice_date=fields.Date.today(),
                    partner_id=self.env.ref("base.res_partner_3").id,
                    journal_id=self.purchase_journal.id,
                    invoice_line_ids=[
                        (
                            0,
                            0,
                            {
                                "product_id": self.env.ref(
                                    "product.product_product_5"
                                ).id,
                                "quantity": 10.0,
                                "price_unit": 450.0,
                                "account_id": self.env["account.account"]
                                .search(
                                    [
                                        (
                                            "user_type_id",
                                            "=",
                                            self.env.ref(
                                                "account.data_account_type_revenue"
                                            ).id,
                                        ),
                                        (
                                            "company_id",
                                            "=",
                                            self.env.company.id,
                                        ),
                                    ],
                                    limit=1,
                                )
                                .id,
                                "name": "product test 5",
                                "uom_id": self.env.ref("uom.product_uom_unit").id,
                            },
                        )
                    ],
                )
            )
            for mock_call in mocked_env.mock_calls:
                if (
                    str(mock_call.args[0]).split(".")[:-1] == ["account", "move"]
                    and mock_call.args[1]
                    and not isinstance(mock_call.args[1][0].id, NewId)
                ):
                    self.assertEqual(mock_call.args[1], invoice)
                elif (
                    str(mock_call.args[0]).split(".")[:-1]
                    == ["account", "move", "line"]
                    and mock_call.args[1]
                    and not isinstance(mock_call.args[1][0].id, NewId)
                ):
                    for line in mock_call.args[1]:
                        self.assertIn(line, invoice.line_ids)

    def test_write_dont_recompute_existing_moves(self):
        with mock.patch.object(
            self.env.__class__, "add_to_compute", wraps=None
        ) as mocked_env:
            self.invoice_1.invoice_line_ids[0].write({"quantity": 20})

            for mock_call in mocked_env.mock_calls:
                if (
                    str(mock_call.args[0]).split(".")[:-1] == ["account", "move"]
                    and mock_call.args[1]
                    and not isinstance(mock_call.args[1][0].id, NewId)
                ):
                    self.assertEqual(mock_call.args[1], self.invoice_1)
                elif (
                    str(mock_call.args[0]).split(".")[:-1]
                    == ["account", "move", "line"]
                    and mock_call.args[1]
                    and not isinstance(mock_call.args[1][0].id, NewId)
                ):
                    for line in mock_call.args[1]:
                        self.assertIn(line, self.invoice_1.line_ids)

    def test_state(self):
        self.assertEqual(
            self.invoice_1.state, "draft", "Invoice should be in state Draft"
        )
        self.invoice_1.action_post()
        self.assertEqual(
            self.invoice_1.state, "posted", "Invoice should be in state posted"
        )
