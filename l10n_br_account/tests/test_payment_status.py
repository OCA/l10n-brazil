# Copyright 2025 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import Form, tagged

from odoo.addons.test_mail.tests.common import TestMailCommon

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestPaymentStatusBR(AccountMoveBRCommon, TestMailCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Enable tracking (needed by this scenario)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=False))
        cls.configure_normal_company_taxes()

    def test_payment_status_partial_paid_partial(self):
        invoice = self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )
        invoice.action_post()
        self.assertEqual(invoice.payment_state, "not_paid")
        self.assertEqual(invoice.amount_residual, 1032.5)

        # First partial payment
        self._register_payment(invoice, 600.0)
        self.assertEqual(invoice.payment_state, "partial")

        # Second partial payment (completes amount)
        pmt2 = self._register_payment(invoice, 432.5)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertEqual(invoice.amount_residual, 0.0)
        self.flush_tracking()

        # Remove pmt2 partial reconciliation and assert effects
        def _is_receivable(line):
            return line.account_id.account_type == "asset_receivable"

        inv_recv = invoice.line_ids.filtered(_is_receivable)
        pay_recv = pmt2.line_ids.filtered(_is_receivable)
        partial_to_remove = inv_recv.matched_credit_ids & pay_recv.matched_debit_ids
        invoice.js_remove_outstanding_partial(partial_to_remove.id)

        self.assertEqual(invoice.amount_residual, 432.5)
        self.assertEqual(invoice.payment_state, "partial")

    def _register_payment(self, invoice, amount):
        bank_journal = self.company_data["default_journal_bank"]
        with Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            )
        ) as wiz_form:
            wiz_form.journal_id = bank_journal
            wiz_form.payment_date = fields.Date.today()
            wiz_form.amount = amount
        wiz = wiz_form.save()
        payments = wiz._create_payments()
        return payments
