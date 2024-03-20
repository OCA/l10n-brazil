# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from openerp.tests.common import TransactionCase
from openerp.exceptions import UserError, ValidationError


class TestPaymentOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        # Get Invoice for test
        self.invoice_customer_original = self.env.ref(
            'l10n_br_account_payment_order.demo_invoice_payment_order'
        )

        # Payment Mode
        self.payment_mode = self.env.ref(
            'l10n_br_account_payment_order.main_company_payment_mode_boleto'
        )

        self.env['account.payment.order'].search([])

        # Configure to be possibile create Payment Order
        self.payment_mode.payment_order_ok = True

        self.invoice_customer_original.payment_mode_id = self.payment_mode.id

        # Configure Journal to update posted
        self.invoice_customer_original.journal_id.update_posted = True

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.invoice_customer_original.state, 'draft')

        # I validate invoice by creating on
        self.invoice_customer_original.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.invoice_customer_original.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.invoice_customer_original.move_id,\
            "Move not created for open invoice"

    def test_implemented_fields_payment_order(self):
        """ Test implemented fields in object account.move.line """
        # Check Payment Mode field
        assert self.invoice_customer_original.payment_mode_id, \
            "Payment Mode field is not filled."

        # Change status of Move to draft just to test
        self.invoice_customer_original.move_id.button_cancel()

        for line in self.invoice_customer_original.move_id.line_ids.filtered(
                lambda l: l.account_id.id ==
                self.invoice_customer_original.account_id.id):
            self.assertEqual(
                line.journal_entry_ref, line.invoice_id.name,
                "Error with compute field journal_entry_ref")
            test_balance_value = line.get_balance()

        # Return the status of Move to Posted
        self.invoice_customer_original.move_id.action_post()

        for line in self.invoice_customer_original.move_id.line_ids.filtered(
                lambda l: l.account_id.id ==
                self.invoice_customer_original.account_id.id):
            self.assertEqual(
                line.journal_entry_ref, line.invoice_id.name,
                "Error with compute field journal_entry_ref")
            test_balance_value = line.get_balance()

        self.assertEqual(
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

        self.assertEqual(len(payment_order.payment_line_ids), 2)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        for line in payment_order.payment_line_ids:
            line.percent_interest = 1.5
            self.assertEqual(line._get_info_partner(
                self.invoice_customer_original.partner_id),
                'AKRETION LTDA',
                "Error with method _get_info_partner"
            )
            test_amount_interest = line.amount_interest
        self.assertEqual(
            test_amount_interest, 10.5,
            "Error with compute field amount_interest.")

        # Open payment order
        payment_order.draft2open()

        self.assertEqual(len(payment_order.bank_line_ids), 2)

        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(payment_order.state, 'uploaded')
        with self.assertRaises(UserError):
            payment_order.unlink()

        bank_line = payment_order.bank_line_ids

        with self.assertRaises(UserError):
            bank_line.unlink()

        payment_order.action_done_cancel()
        self.assertEqual(payment_order.state, 'cancel')

        payment_order.unlink()
        self.assertEqual(len(self.env['account.payment.order'].search([])), 0)

    def test_bra_number_constrains(self):
        """ Test bra_number constrains. """
        self.banco_bradesco = self.env[
            'res.bank'].search([('code_bc', '=', '033')])
        with self.assertRaises(ValidationError):
            self.env[
                'res.partner.bank'].create(dict(
                    bank_id=self.banco_bradesco.id,
                    partner_id=self.ref('l10n_br_base.res_partner_akretion'),
                    bra_number='12345'
                ))
