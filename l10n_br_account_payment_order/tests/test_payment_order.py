# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.tests.common import TransactionCase
from openerp.exceptions import UserError


class TestPaymentOrder(TransactionCase):

    def setUp(self):
        super(TestPaymentOrder, self).setUp()

        self.invoice_customer_original = self.env.ref(
            'l10n_br_account_banking_payment.demo_invoice_payment_order'
        )

        # Payment Mode
        self.payment_mode = self.env.ref(
            'account_payment_mode.payment_mode_inbound_ct1'
        )

        # Configure to be possibile create Payment Order
        self.payment_mode.payment_order_ok = True

        self.invoice_customer_original.payment_mode_id = self.payment_mode.id

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.invoice_customer_original.state, 'draft')

        # I change the state of invoice to "Proforma2" by clicking
        # PRO-FORMA button
        self.invoice_customer_original.action_invoice_proforma2()

        # I check that the invoice state is now "Proforma2"
        self.assertEquals(self.invoice_customer_original.state, 'proforma2')

        # I check that there is no move attached to the invoice
        self.assertEquals(len(self.invoice_customer_original.move_id), 0)

        # I validate invoice by creating on
        self.invoice_customer_original.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_customer_original.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.invoice_customer_original.move_id,\
            "Move not created for open invoice"

    def test_implemented_fields_payment_order(self):
        """ Test implemented fields in object account.move.line """
        # Check Payment Mode field
        assert self.invoice_customer_original.payment_mode_id, \
            "Payment Mode field is not filled."
        for line in self.invoice_customer_original.move_id.line_ids.filtered(
                lambda l: l.account_id.id ==
                self.invoice_customer_original.account_id.id):
            self.assertEquals(
                line.journal_entry_ref, 'INV/2019/0004',
                "Error with compute field journal_entry_ref")
            test_balance_value = line.get_balance()
        self.assertEquals(
            test_balance_value, 700.0,
            "Error with method get_balance()")

    def test_cancel_payment_order(self):
        """ Test create and cancel a Payment Order."""
        # Add to payment order
        self.invoice_customer_original.create_account_payment_line()

        payment_order = self.env['account.payment.order'].search([])
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        # Set journal to allow cancelling entries
        bank_journal.update_posted = True

        payment_order.write({
            'journal_id': bank_journal.id
        })

        self.assertEquals(len(payment_order.payment_line_ids), 2)
        self.assertEquals(len(payment_order.bank_line_ids), 0)

        for line in payment_order.payment_line_ids:
            line.percent_interest = 1.5
            self.assertEquals(line._get_info_partner(
                self.invoice_customer_original.partner_id),
                'AKRETION LTDA',
                "Error with method _get_info_partner"
            )
            test_amount_interest = line.amount_interest
        self.assertEquals(
            test_amount_interest, 10.5,
            "Error with compute field amount_interest.")

        # Open payment order
        payment_order.draft2open()

        self.assertEquals(len(payment_order.bank_line_ids), 2)

        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEquals(payment_order.state, 'uploaded')
        with self.assertRaises(UserError):
            payment_order.unlink()

        bank_line = payment_order.bank_line_ids

        with self.assertRaises(UserError):
            bank_line.unlink()

        payment_order.action_done_cancel()
        self.assertEquals(payment_order.state, 'cancel')

        payment_order.unlink()
        self.assertEquals(len(self.env['account.payment.order'].search([])), 0)
