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

        # Product Tax Boleto
        self.invoice_product_tax_boleto = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order_bb_cnab400'
        )

        # Product Tax Boleto
        self.invoice_cheque = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order_cheque'
        )

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

    def test_product_tax_boleto(self):
        """ Test Invoice where Payment Mode has Product Tax. """
        self.invoice_product_tax_boleto._onchange_payment_mode_id()
        # I validate invoice by creating on
        self.invoice_customer_original.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_customer_original.state, 'open')

    def test_payment_mode_without_payment_order(self):
        """ Test Invoice when Payment Mode not generate Payment Order. """
        self.invoice_cheque._onchange_payment_mode_id()
        # I validate invoice by creating on
        self.invoice_cheque.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_cheque.state, 'open')
