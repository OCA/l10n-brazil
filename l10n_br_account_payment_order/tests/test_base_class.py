# Copyright (C) 2021-Today - KMEE (<http://kmee.com.br>).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrAccountPaymentOder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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

    def _send_new_cnab_code(
        self,
        aml_to_change,
        code_to_send,
        warning_error=False,
    ):
        with Form(
            self.env["account.move.line.cnab.change"].with_context(
                **dict(
                    active_ids=aml_to_change.ids,
                    active_model="account.move.line",
                )
            ),
            view=self.chance_view_id,
        ) as f:
            f.change_type = code_to_send
            if code_to_send == "change_date_maturity":
                new_date = date.today() + relativedelta(years=1)
                payment_cheque = self.env.ref(
                    "l10n_br_account_payment_order." "payment_mode_cheque"
                )

                if warning_error and aml_to_change.payment_mode_id != payment_cheque:
                    # Testa caso Sem Codigo
                    new_date = aml_to_change.date_maturity
                # Testa caso com Codigo e Data de Vencimento igual
                f.date_maturity = new_date
            if code_to_send == "grant_rebate":
                f.rebate_value = 10.00
            if code_to_send == "grant_discount":
                f.discount_value = 10.00

        change_wizard = f.save()

        if warning_error:
            with self.assertRaises(UserError):
                change_wizard.doit()
        else:
            change_wizard.doit()

    def _send_and_check_new_cnab_code(
        self,
        invoice,
        aml_to_change,
        code_to_send,
        xml_code=False,
        warning_error=False,
    ):
        self._send_new_cnab_code(aml_to_change, code_to_send, warning_error)

        if not warning_error:
            change_payment_order = self.env["account.payment.order"].search(
                [
                    ("state", "=", "draft"),
                    ("payment_mode_id", "=", invoice.payment_mode_id.id),
                ]
            )
            self._payment_order_all_workflow(change_payment_order)

            assert (
                self.env.ref(xml_code).id
                in change_payment_order.payment_line_ids.mapped(
                    "instruction_move_code_id"
                ).ids
            ), f"Payment Order with wrong instruction_move_code_id for {code_to_send}"
