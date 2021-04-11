# @ 2021 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import date
from datetime import timedelta

from odoo.tests import Form
from odoo.tests import SavepointCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPaymentOrderInbound(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.move_line_change_id = self.env['account.move.line.cnab.change']

        self.demo_invoice_change = self.env.ref(
            'l10n_br_account_payment_order.'
            'demo_invoice_change'
        )

    def test_change_due_date(self):
        """ Test Create Payment Order """

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.demo_invoice_change.state, 'draft')

        # I validate invoice by creating on
        self.demo_invoice_change.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.demo_invoice_change.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.demo_invoice_change.move_id,\
            "Move not created for open invoice"
        inv_payment_mode_id = \
            self.demo_invoice_change.payment_mode_id
        payment_order = self.env['account.payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', inv_payment_mode_id.id)
        ])
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()
        payment_order.action_done()

        date_maturity = self.demo_invoice_change. \
            financial_move_line_ids.mapped('date_maturity')

        ctx = {
            'active_ids':
                self.demo_invoice_change
                    .financial_move_line_ids.ids,
            'active_model': 'account.move.line'
        }
        new_date = date.today() + timedelta(days=120)
        view_id = 'l10n_br_account_payment_order.' \
                  'account_move_line_cnab_change_form_view'
        with Form(self.move_line_change_id.with_context(ctx),
                  view=view_id) as f:
            f.change_type = 'change_date_maturity'
            f.date_maturity = new_date
        change_wizard = f.save()
        change_wizard.doit()

        self.assertEqual(
            self.demo_invoice_change.financial_move_line_ids[0].date_maturity,
            new_date,
            'Data não alterada'
        )
        self.assertNotEqual(
            date_maturity[0],
            new_date,
            'Data não alterada'
        )

        change_payment_order = self.env['account.payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', inv_payment_mode_id.id)
        ])

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()
        change_payment_order.action_done()

        assert self.env.ref(
            'l10n_br_account_payment_order.manual_test_mov_instruction_code_06'
        ).id in change_payment_order.payment_line_ids.mapped(
            'mov_instruction_code_id'
        ).ids, "Payment Order with wrong mov_instruction_code_id"
