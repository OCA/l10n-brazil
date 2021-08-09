# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged

from .test_base_class import TestL10nBrAccountPaymentOder


@tagged("post_install", "-at_install")
class TestPaymentOrderManualWorkflow(TestL10nBrAccountPaymentOder):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Get Invoice for test
        cls.invoice_manual_test = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_manual_test"
        )

    def _invoice_confirm_flow(self):
        self.invoice_manual_test.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.invoice_manual_test.state, "open")

    def test_invoice_button(self):
        """ Test Invoice Button to Add to a payment order"""
        self._invoice_confirm_flow()
        self.invoice_manual_test.create_account_payment_line()
        self._invoice_payment_order_all_workflow(self.invoice_manual_test)

    def test_payment_order_wizard(self):
        """ Test Payment Order Wizard"""
        self._invoice_confirm_flow()
        payment_mode_id = self.invoice_manual_test.payment_mode_id
        self.import_with_po_wizard(payment_mode_id)
