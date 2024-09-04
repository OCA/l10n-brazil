# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>

from datetime import datetime, time, timedelta

from pytz import UTC, timezone

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_PARTNER


class TestInvoiceDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        # set default user company
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [(6, 0, companies.ids)]
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
            (
                0,
                0,
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

    def test_document_date(self):
        self.move_id.issuer = DOCUMENT_ISSUER_PARTNER
        user_tz = timezone(self.env.user.tz or "UTC")
        original_date = datetime.combine(datetime.now().date(), time.min)
        # Convert the original_date to the user's timezone and remove the time for
        # comparison
        original_date_in_user_tz = (
            user_tz.localize(original_date).astimezone(UTC).replace(tzinfo=None)
        )
        original_date_without_time = original_date_in_user_tz.date()

        self.move_id.invoice_date = original_date.date()
        self.move_id.fiscal_document_id._compute_document_date()

        self.assertEqual(
            self.move_id.fiscal_document_id.document_date.date(),
            original_date_without_time,
            "Computed document date is incorrect",
        )

    def test_inverse_document_date(self):
        self.move_id.issuer = DOCUMENT_ISSUER_PARTNER
        new_date = datetime.now() - timedelta(days=2)
        self.move_id.fiscal_document_id.document_date = new_date
        self.move_id.fiscal_document_id._inverse_document_date()

        self.assertEqual(
            self.move_id.invoice_date,
            new_date.date(),
            "Inverse computed invoice date is incorrect",
        )

    def test_date_in_out(self):
        self.move_id.issuer = DOCUMENT_ISSUER_PARTNER
        user_tz = timezone(self.env.user.tz or "UTC")
        original_date = datetime.combine(datetime.now().date(), time.min)
        # Convert the original_date to the user's timezone and remove the time for
        # comparison
        original_date_in_user_tz = (
            user_tz.localize(original_date).astimezone(UTC).replace(tzinfo=None)
        )
        original_date_without_time = original_date_in_user_tz.date()
        self.move_id.date = original_date.date()
        self.move_id.fiscal_document_id._compute_date_in_out()

        self.assertEqual(
            self.move_id.fiscal_document_id.date_in_out.date(),
            original_date_without_time,
            "Computed date in out is incorrect",
        )

    def test_inverse_date_in_out(self):
        self.move_id.issuer = DOCUMENT_ISSUER_PARTNER
        new_date = datetime.now() - timedelta(days=2)
        self.move_id.fiscal_document_id.date_in_out = new_date
        self.move_id.fiscal_document_id._inverse_date_in_out()
        self.assertEqual(
            self.move_id.date,
            new_date.date(),
            "Inverse computed account date is incorrect",
        )
