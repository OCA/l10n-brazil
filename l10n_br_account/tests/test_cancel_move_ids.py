# Copyright 2026 - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestCancelMoveIds(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.invoice = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

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
        return wiz._create_payments()

    def test_cancel_move_ids_clears_reconciliation(self):
        self.invoice.action_post()
        self.assertEqual(self.invoice.payment_state, "not_paid")
        residual_before_payment = self.invoice.amount_residual

        payment = self._register_payment(self.invoice, residual_before_payment)
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertEqual(self.invoice.amount_residual, 0.0)

        def _receivable(line):
            return line.account_id.account_type == "asset_receivable"

        inv_recv = self.invoice.line_ids.filtered(_receivable)
        pay_recv = payment.line_ids.filtered(_receivable)
        self.assertTrue(pay_recv.reconciled)
        partials = inv_recv.matched_credit_ids | inv_recv.matched_debit_ids
        self.assertTrue(partials)

        self.invoice.fiscal_document_id.cancel_move_ids()

        self.assertEqual(self.invoice.state, "cancel")
        self.assertFalse(pay_recv.reconciled)
        self.assertFalse(inv_recv.reconciled)
        self.assertFalse(payment.is_reconciled)
        self.assertFalse(inv_recv.matched_credit_ids | inv_recv.matched_debit_ids)
        self.assertFalse(partials.exists())

    def test_cancel_move_ids_clears_analytic_lines(self):
        """Regression for OCA/l10n-brazil#3217."""
        plan = self.env["account.analytic.plan"].create({"name": "Test Plan"})
        analytic_account = self.env["account.analytic.account"].create(
            {"name": "Test Analytic Account", "plan_id": plan.id}
        )
        product_line = self.invoice.invoice_line_ids[:1]
        product_line.analytic_distribution = {str(analytic_account.id): 100.0}
        self.invoice.action_post()

        analytic_lines = self.env["account.analytic.line"].search(
            [("move_line_id", "in", self.invoice.line_ids.ids)]
        )
        self.assertTrue(analytic_lines)

        self.invoice.fiscal_document_id.cancel_move_ids()

        self.assertFalse(analytic_lines.exists())

    def test_cancel_move_ids_idempotent(self):
        self.invoice.action_post()
        self.invoice.fiscal_document_id.cancel_move_ids()
        self.assertEqual(self.invoice.state, "cancel")
        self.invoice.fiscal_document_id.cancel_move_ids()
        self.assertEqual(self.invoice.state, "cancel")

    def test_document_cancel_blocks_on_lock_date_before_sefaz(self):
        # Calls the full _document_cancel entry point so the test fails if
        # the preflight ever gets dropped from the chain.
        self.invoice.action_post()
        self.invoice.company_id.fiscalyear_lock_date = self.invoice.invoice_date
        document = self.invoice.fiscal_document_id
        state_edoc_before = document.state_edoc

        with self.assertRaises(UserError):
            document._document_cancel("Test cancellation with more than 15 chars")

        self.assertEqual(document.state_edoc, state_edoc_before)
        self.assertEqual(self.invoice.state, "posted")

    def test_cancel_move_ids_preserves_state_edoc(self):
        # Guards against naively reusing button_draft, which would trigger
        # action_document_back2draft and regress state_edoc.
        self.invoice.action_post()
        document = self.invoice.fiscal_document_id
        document.flush_recordset()
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET state_edoc = 'cancelada' "
            "WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["state_edoc"])
        self.assertEqual(document.state_edoc, "cancelada")

        document.cancel_move_ids()

        self.assertEqual(self.invoice.state, "cancel")
        self.assertEqual(document.state_edoc, "cancelada")
