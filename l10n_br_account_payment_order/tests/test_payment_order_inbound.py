# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# @ 2020 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
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

    def test_payment_inbound_change_due_date(self):
        """ Change account.move.line due date. Automatic add this aml to a new
        payment.order, export the movement to the bank and process it's accept return.
        :return:
        """
        pass

    def test_payment_inbound_cancel_invoice_not_registred(self):
        """ Cancel the invoice with a payment that isn't registred at the bank
        :return:
        """
        pass

    def test_payment_inbound_cancel_invoice_alread_registred_raise(self):
        """ Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" before you can cancel
        the invoice.

        In this test we must get a raise when trying to cancel the invoice.

        :return:
        """
        pass

    def test_payment_inbound_payment_in_cash(self):
        """ Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        pass

    def test_payment_inbound_cancel_invoice_alread_registred_with_baixa(self):
        """ Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" before you can cancel
        the invoice.
        :return:
        """
        pass

    def test_payment_inbound_return_accept(self):
        """ The payment was exported and the bank return that it's accepted
        :return:
        """
        pass

    def test_payment_inbound_return_denied(self):
        """ The payment was exported and the bank return that it's denied
        :return:
        """
        pass

    def test_payment_inbound_return_paid(self):
        """ The payment was exported, accepted, and after some days the bank
        return that it's paid (LIQUIDADO) by the customer
        :return:
        """
        pass

    def test_payment_inbound_return_paid_with_interest(self):
        """ The payment was exported, accepted, and after some days the bank
        return that it's paid (LIQUIDADO) by the customer but with interest
        :return:
        """
        pass

    def test_payment_inbound_return_paid_with_discount(self):
        """ The payment was exported, accepted, and after some days the bank
        return that it's paid (LIQUIDADO) by the customer but with discount
        :return:
        """
        pass

    def test_payment_inbound_protesto(self):
        """ Protesto movement sent and accepted
        :return:
        """
        pass
