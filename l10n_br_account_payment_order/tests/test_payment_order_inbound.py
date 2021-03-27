# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# @ 2020 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tests import tagged
from odoo.tests import SavepointCase


@tagged('post_install', '-at_install')
class TestPaymentOrderInbound(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        # Product Tax Boleto
        self.invoice_product_tax_boleto = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order_bb_cnab400'
        )

        # Product Tax Boleto
        self.invoice_cheque = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order_cheque'
        )

    def test_product_tax_boleto(self):
        """ Test Invoice where Payment Mode has Product Tax. """
        self.invoice_product_tax_boleto._onchange_payment_mode_id()

        # Produto Taxa adicionado
        line_product_tax = self.invoice_product_tax_boleto.\
            invoice_line_ids.filtered(
                lambda l: l.product_id == self.invoice_product_tax_boleto.
                payment_mode_id.product_tax_id)

        self.assertEquals(len(line_product_tax), 1)
        # I validate invoice by creating on
        self.invoice_product_tax_boleto.action_invoice_open()
        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_product_tax_boleto.state, 'open')

    def test_payment_mode_without_payment_order(self):
        """ Test Invoice when Payment Mode not generate Payment Order. """
        self.invoice_cheque._onchange_payment_mode_id()
        # I validate invoice by creating on
        self.invoice_cheque.action_invoice_open()
        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_cheque.state, 'open')
        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cheque.payment_mode_id.id)
        ])
        self.assertEquals(len(payment_order), 0)

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

    def test_payment_inbound_return_baixado(self):
        """ The payment was exported, accepted, and after some days the user at
         internet banking cancel it (STATE: BAIXADO). The invoice must stay
         open, waiting to the user to do a new manual action.

          - The user must be warned that the state of the invoice/aml
            was changed at the bank;
          - The user can record manual/statement payment with another payment method;
          - The user can cancel the invoice/aml;

         This test is similar with "test_payment_inbound_payment_in_cash" buy
         it is not exported again to the bank because i'ts already set manualy at the
         internet banking
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
