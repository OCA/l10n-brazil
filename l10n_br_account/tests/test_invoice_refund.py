# Copyright (C) 2021  Ygor Carvalho - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestInvoiceRefund(TransactionCase):
    def setUp(self):
        super().setUp()

        self.sale_account = self.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Refund Sales - (test)",
                user_type_id=self.env.ref("account.data_account_type_revenue").id,
                reconcile=True,
            )
        )

        self.refund_journal = self.env["account.journal"].create(
            dict(
                name="Refund Journal - (test)",
                code="TREJ",
                type="sale",
                refund_sequence=True,
                default_debit_account_id=self.sale_account.id,
                default_credit_account_id=self.sale_account.id,
                update_posted=True,
            )
        )

        self.invoice = self.env["account.invoice"].create(
            dict(
                name="Test Refund Invoice",
                payment_term_id=self.env.ref("account.account_payment_term_advance").id,
                partner_id=self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                journal_id=self.refund_journal.id,
                document_type_id=self.env.ref("l10n_br_fiscal.document_55").id,
                document_serie_id=self.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_6").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
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
                                        self.env.user.company_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "Refund Test",
                            "uom_id": self.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            )
        )

    def test_refund(self):
        invoice = self.invoice
        self.assertEqual(
            invoice.state,
            "draft",
            "Invoice should be in state Draft",
        )

        invoice.action_invoice_open()
        self.assertEqual(
            invoice.state,
            "open",
            "Invoice should be in state Open",
        )

        invoice._get_refund_common_fields()

        # First functionality error, when there is no transaction registered on
        #   the Invoice.
        with self.assertRaises(UserError):
            invoice.refund()

        invoice["fiscal_operation_id"] = (self.env.ref("l10n_br_fiscal.fo_venda").id,)

        # Second functionality error, when there is a fiscal operation, but there
        #   is no fiscal operation line.
        with self.assertRaises(UserError):
            invoice.refund()

        for line_id in invoice.invoice_line_ids:
            line_id["fiscal_operation_id"] = (
                self.env.ref("l10n_br_fiscal.fo_venda").id,
            )
            line_id["fiscal_operation_line_id"] = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            ).id

        new_invoice = invoice.refund()

        # What is being done here is just confirming whether were successful in the
        #   process of creating the new invoice with the corresponding tax return
        #   operation. As the original is a Sales operation, its inverse would be
        #   Sales Return.
        self.assertEqual(
            new_invoice.operation_name,
            "Devolução de Venda",
            "The refund process was unsuccessful.",
        )
