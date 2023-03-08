# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import SavepointCase, tagged
from odoo.tests.common import Form


@tagged("post_install", "-at_install")
class TestPaymentOrder(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Get Invoice for test
        cls.invoice_customer_without_paymeny_mode = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_no_payment_mode"
        )
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        cls.main_company = cls.env.ref("base.main_company")
        cls.journal_cash = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.main_company.id)], limit=1
        )

    def test_cancel_invoice_no_payment_mode_pay(self):
        """Test Pay Invoice without payment mode in cash"""

        # I check that the invoice state is "posted"
        self.assertEqual(self.invoice_customer_without_paymeny_mode.state, "posted")

        open_amount = self.invoice_customer_without_paymeny_mode.amount_residual
        # I totally pay the Invoice
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice_customer_without_paymeny_mode.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 300 instead of 500
        payment_register.amount = open_amount

        payment = payment_register.save()._create_payments()
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.invoice_customer_without_paymeny_mode.payment_state,
            "paid",
            "Invoice is not in Paid state",
        )

    def test_cancel_invoice_no_payment_mode_cancel(self):
        """Test Cancel Invoice Without Payment Mode"""
        self.invoice_customer_without_paymeny_mode.button_cancel()

        # I check that the invoice state is "Cancel"
        self.assertEqual(self.invoice_customer_without_paymeny_mode.state, "cancel")
