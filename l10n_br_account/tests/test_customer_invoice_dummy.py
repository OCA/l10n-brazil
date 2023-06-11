# Copyright (C) 2018 - Magno Costa - Akretion
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.models import NewId
from odoo.tests import SavepointCase


class TestCustomerInvoice(SavepointCase):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with customer invoices.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Sales - (test)",
                user_type_id=cls.env.ref("account.data_account_type_revenue").id,
                reconcile=True,
            )
        )

        cls.sale_journal = cls.env["account.journal"].create(
            dict(
                name="Sales Journal - (test)",
                code="TSAJ",
                type="sale",
                refund_sequence=True,
                default_account_id=cls.sale_account.id,
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
                name="Test Customer Invoice 1",
                move_type="out_invoice",
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
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

        # Invoice with TAXES
        tax_fixed = cls.env["account.tax"].create(
            {
                "sequence": 10,
                "name": "Tax 10.0 (Fixed)",
                "amount": 10.0,
                "amount_type": "fixed",
                "include_base_amount": True,
            }
        )

        tax_percent_included_base_incl = cls.env["account.tax"].create(
            {
                "sequence": 20,
                "name": "Tax 50.0% (Percentage of Price Tax Included)",
                "amount": 50.0,
                "amount_type": "division",
                "include_base_amount": True,
            }
        )

        tax_percentage = cls.env["account.tax"].create(
            {
                "sequence": 30,
                "name": "Tax 20.0% (Percentage of Price)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
            }
        )

        cls.invoice_2 = cls.env["account.move"].create(
            dict(
                name="Test Customer Invoice 2",
                move_type="out_invoice",
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_5").id,
                            "quantity": 5.0,
                            "price_unit": 100.0,
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
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        tax_fixed.id,
                                        tax_percent_included_base_incl.id,
                                        tax_percentage.id,
                                    ],
                                )
                            ],
                        },
                    )
                ],
            )
        )

        tax_discount = cls.env["account.tax"].create(
            {
                "sequence": 40,
                "name": "Tax 20.0% (Discount)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
            }
        )

        cls.invoice_3 = cls.env["account.move"].create(
            dict(
                name="Test Customer Invoice 3",
                move_type="out_invoice",
                currency_id=cls.env.ref("base.EUR").id,
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
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
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        tax_discount.id,
                                        tax_percent_included_base_incl.id,
                                        tax_percentage.id,
                                    ],
                                )
                            ],
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
                    name="Test Customer Invoice 1",
                    move_type="out_invoice",
                    partner_id=self.env.ref("base.res_partner_3").id,
                    journal_id=self.sale_journal.id,
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

    def test_post(self):
        self.invoice_2.action_post()
        self.assertEqual(
            self.invoice_2.state, "posted", "Invoice should be in state posted"
        )

    def test_invoice_other_currency(self):
        self.assertEqual(
            self.invoice_3.state, "draft", "Invoice should be in state Draft"
        )
        self.invoice_3.action_post()
        self.assertEqual(
            self.invoice_3.state, "posted", "Invoice should be in state posted"
        )

    def test_line_ids_write(self):
        self.invoice_3.invoice_line_ids.write({"move_id": self.invoice_3.id})
        for line in self.invoice_3.invoice_line_ids:
            self.assertEqual(
                line.document_id.id,
                self.invoice_3.fiscal_document_id.id,
                "line.document_id should be equal invoice fiscal_document_id",
            )

    def test_invoice_copy_with_dummy(self):
        """
        Tests the functionality of copying an invoice while using a fiscal dummy.
        It verifies that the new invoice isn't recognized as a fiscal document,
        the same fiscal dummy is used, and that no new entries were created.
        """

        # Retrieve initial count of fiscal document lines
        init_number_of_fiscal_doc_lines = self.env[
            "l10n_br_fiscal.document.line"
        ].search_count([])

        invoice_copy = self.invoice_1.copy()

        # Confirm that the copied invoice uses the fiscal dummy
        self.assertFalse(self.invoice_1.document_type_id.exists())
        self.assertFalse(invoice_copy.document_type_id.exists())

        # Check that no new fiscal document lines were created after copying the invoice
        final_number_of_fiscal_doc_lines = self.env[
            "l10n_br_fiscal.document.line"
        ].search_count([])
        self.assertEqual(
            init_number_of_fiscal_doc_lines, final_number_of_fiscal_doc_lines
        )

        # Retrieve the dummy fiscal document line
        dummy_fiscal_document_line = (
            self.invoice_1.company_id.fiscal_dummy_id.fiscal_line_ids[0]
        )

        # Check that all account move lines are associated with the fiscal dummy
        for line in invoice_copy.line_ids:
            self.assertEqual(
                line.fiscal_document_line_id.id, dummy_fiscal_document_line.id
            )

        self.assertEqual(len(invoice_copy), 1)
