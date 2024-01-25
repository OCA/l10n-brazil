# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>

from odoo.tests import TransactionCase


class TestInvoiceDiscount(TransactionCase):
    def setUp(self):
        super().setUp()

        self.company = self.env.ref("l10n_br_base.empresa_lucro_presumido")

        # set default user company
        companies = self.env["res.company"].search([])
        self.env.user.company_ids = [(6, 0, companies.ids)]
        self.env.user.company_id = self.company

        self.invoice_account_id = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
                "code": "RECTEST",
                "name": "Test receivable account",
                "reconcile": True,
            }
        )

        self.invoice_journal = self.env["account.journal"].create(
            {
                "company_id": self.company.id,
                "name": "Invoice Journal - (test)",
                "code": "INVTEST",
                "type": "sale",
            }
        )

        self.invoice_line_account_id = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
                "code": "705070",
                "name": "Product revenue account (test)",
            }
        )

        self.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        self.fiscal_operation_id.deductible_taxes = True

        product_id = self.env.ref("product.product_product_7")

        invoice_line_vals = [
            (
                0,
                0,
                {
                    "account_id": self.invoice_line_account_id.id,
                    "product_id": product_id.id,
                    "quantity": 1,
                    "price_unit": 1000.0,
                    "discount_value": 100.0,
                },
            )
        ]

        self.move_id = (
            self.env["account.move"]
            .with_context(check_move_validity=False)
            .create(
                {
                    "company_id": self.company.id,
                    "document_serie_id": self.env.ref(
                        "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                    ).id,
                    "journal_id": self.invoice_journal.id,
                    "invoice_user_id": self.env.user.id,
                    "fiscal_operation_id": self.fiscal_operation_id,
                    "move_type": "out_invoice",
                    "currency_id": self.company.currency_id.id,
                    "invoice_line_ids": invoice_line_vals,
                }
            )
        )

    def test_discount(self):
        self.assertEqual(self.move_id.invoice_line_ids.price_unit, 1000)
        self.assertEqual(self.move_id.invoice_line_ids.quantity, 1)
        self.assertEqual(self.move_id.invoice_line_ids.discount_value, 100)
        self.assertEqual(self.move_id.invoice_line_ids.discount, 10)
        self.move_id.invoice_line_ids._onchange_price_subtotal()
        self.assertEqual(self.move_id.invoice_line_ids.price_subtotal, 900)
