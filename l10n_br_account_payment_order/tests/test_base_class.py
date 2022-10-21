# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrAccountPaymentOder(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.move_line_change_id = cls.env["account.move.line.cnab.change"]

        cls.chance_view_id = (
            "l10n_br_account_payment_order." "account_move_line_cnab_change_form_view"
        )

    def _payment_order_all_workflow(self, payment_order_id):
        """Run all Payment Order Workflow"""
        payment_order_id.draft2open()
        payment_order_id.open2generated()
        payment_order_id.generated2uploaded()

    def _invoice_payment_order_all_workflow(self, invoice):
        """Search for the payment order related to the invoice"""
        payment_order_id = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", invoice.payment_mode_id.id),
            ]
        )
        assert payment_order_id, "Payment Order not created."
        self._payment_order_all_workflow(payment_order_id)
        return payment_order_id

    def _prepare_change_view(self, financial_move_line_ids):
        """Prepare context of the change view"""
        ctx = dict(
            active_ids=financial_move_line_ids.ids, active_model="account.move.line"
        )
        return self.move_line_change_id.with_context(**ctx)

    def import_with_po_wizard(self, payment_mode_id, payment_type="inbound", aml=False):
        order_vals = {
            "payment_type": payment_type,
            "payment_mode_id": payment_mode_id.id,
        }
        order = self.env["account.payment.order"].create(order_vals)
        with self.assertRaises(UserError):
            order.draft2open()
        order.payment_mode_id_change()
        self.assertEqual(order.journal_id.id, payment_mode_id.fixed_journal_id.id)
        self.assertEqual(len(order.payment_line_ids), 0)

        with self.assertRaises(UserError):
            order.draft2open()

        line_create = (
            self.env["account.payment.line.create"]
            .with_context(active_model="account.payment.order", active_id=order.id)
            .create(
                {"date_type": "move", "move_date": Date.context_today(self.env.user)}
            )
        )
        line_create.payment_mode = "same"
        line_create.move_line_filters_change()
        line_create.populate()
        line_create.create_payment_lines()
        line_created_due = (
            self.env["account.payment.line.create"]
            .with_context(active_model="account.payment.order", active_id=order.id)
            .create(
                {
                    "date_type": "due",
                    "target_move": "all",
                    "due_date": Date.context_today(self.env.user),
                }
            )
        )
        line_created_due.populate()
        line_created_due.create_payment_lines()
        self.assertGreater(len(order.payment_line_ids), 0)
        self._payment_order_all_workflow(order)
        self.assertEqual(order.state, "uploaded")
        return order
