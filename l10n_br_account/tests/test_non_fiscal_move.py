# Copyright (C) 2018 - Magno Costa - Akretion
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestCustomerInvoice(TransactionCase):
    """
    This is a simple test for ensuring non fiscal account.move
    doesn't create fiscal document(.line).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Sales - (test)",
                account_type="income",
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

        cls.init_number_of_fiscal_docs = len(
            cls.env["l10n_br_fiscal.document"].search([])
        )  # NOTE search_count would increment with disabled dummy docs create
        cls.init_number_of_fiscal_doc_lines = len(
            cls.env["l10n_br_fiscal.document.line"].search([])
        )
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
                                        "account_type",
                                        "=",
                                        "income",
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
            len(self.env["l10n_br_fiscal.document"].search([])),
            "Non fiscal invoices should not create fiscal documents"
            "They should use the company dummy document instead.",
        )

    def test_dummy_doc_line_usage(self):
        self.assertEqual(
            self.init_number_of_fiscal_doc_lines,
            len(self.env["l10n_br_fiscal.document.line"].search([])),
            "Non fiscal invoices should not create fiscal document lines"
            "They should use the company dummy document line instead.",
        )

    def test_invoice_copy_with_dummy(self):
        """
        Test the functionality of copying an invoice while using a fiscal dummy.
        Verify that the new invoice isn't recognized as a fiscal document,
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

        # Check that all account move lines are associated with the fiscal dummy
        for line in invoice_copy.line_ids:
            self.assertEqual(line.fiscal_document_line_id.id, False)

        self.assertEqual(len(invoice_copy), 1)
