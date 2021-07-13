# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentOrder(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Get Invoice for test
        cls.invoice_customer_without_paymeny_mode = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_no_payment_mode"
        )

    def test_cancel_invoice_no_payment_mode_pay(self):
        """ Test Pay Invoice without payment mode in cash"""
        self.invoice_customer_without_paymeny_mode.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.invoice_customer_without_paymeny_mode.state, "open")

        open_amount = self.invoice_customer_without_paymeny_mode.residual
        # I totally pay the Invoice
        self.invoice_customer_without_paymeny_mode.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "cash")], limit=1),
            open_amount,
        )

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.invoice_customer_without_paymeny_mode.state,
            "paid",
            "Invoice is not in Paid state",
        )

    def test_cancel_invoice_no_payment_mode_cancel(self):
        """ Test Cancel Invoice Without Payment Mode """
        self.invoice_customer_without_paymeny_mode.action_invoice_cancel()

        # I check that the invoice state is "Cancel"
        self.assertEqual(self.invoice_customer_without_paymeny_mode.state, "cancel")
