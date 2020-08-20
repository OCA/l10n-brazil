# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tests.common import TransactionCase


class TestPaymentOrderInbound(TransactionCase):

    def setUp(self):
        super().setUp()

        # Get Invoice for test
        self.invoice_customer_original = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order'
        )

        self.invoice_customer_original.journal_id.update_posted = True

    def test_payment_order(self):
        """Test automatic creation of Payment Order."""

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.invoice_customer_original.state, 'draft')

        # I validate invoice by creating on
        self.invoice_customer_original.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_customer_original.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.invoice_customer_original.move_id,\
            "Move not created for open invoice"

        payment_order = self.env['account.payment.order'].search([])
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        # The file generation need additional module to use BRCobranca or PyBoleto
        # payment_order.open2generated()
