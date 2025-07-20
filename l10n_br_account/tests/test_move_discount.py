# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>

from odoo import Command
from odoo.tests import TransactionCase


class TestInvoiceDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        # set default user company
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [Command.set(companies.ids)]
        cls.env.user.company_id = cls.company

        cls.invoice_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "account_type": "asset_receivable",
                "code": "RECTEST",
                "name": "Test receivable account",
                "reconcile": True,
            }
        )

        cls.invoice_journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Invoice Journal - (test)",
                "code": "INVTEST",
                "type": "sale",
            }
        )

        cls.invoice_line_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "account_type": "income",
                "code": "705070",
                "name": "Product revenue account (test)",
            }
        )

        cls.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_id.deductible_taxes = True

        product_id = cls.env.ref("product.product_product_7")

        invoice_line_vals = [
            Command.create(
                {
                    "account_id": cls.invoice_line_account_id.id,
                    "product_id": product_id.id,
                    "quantity": 1,
                    "price_unit": 1000.0,
                    "discount_value": 100.0,
                },
            )
        ]

        cls.move_id = (
            cls.env["account.move"]
            .with_context(check_move_validity=False)
            .create(
                {
                    "company_id": cls.company.id,
                    "document_serie_id": cls.env.ref(
                        "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                    ).id,
                    "journal_id": cls.invoice_journal.id,
                    "invoice_user_id": cls.env.user.id,
                    "fiscal_operation_id": cls.fiscal_operation_id.id,
                    "move_type": "out_invoice",
                    "currency_id": cls.company.currency_id.id,
                    "invoice_line_ids": invoice_line_vals,
                }
            )
        )

    def test_discount(self):
        self.assertEqual(self.move_id.invoice_line_ids.price_unit, 1000)
        self.assertEqual(self.move_id.invoice_line_ids.quantity, 1)
        self.assertEqual(self.move_id.invoice_line_ids.discount_value, 100)
        self.assertEqual(self.move_id.invoice_line_ids.discount, 10)
        self.assertEqual(self.move_id.invoice_line_ids.price_subtotal, 900)
