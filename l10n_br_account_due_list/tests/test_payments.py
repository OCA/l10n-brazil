# Copyright (C) 2021 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install_l10n", "post_install", "-at_install")
class TestPayments(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("us")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_01_receivable(self):
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        invoice_form.partner_id = self.partner_a
        invoice_form.ref = "Test l10n_br_account_due_list"
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.price_unit = 200.0
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax_sale_a)
        invoice = invoice_form.save()
        invoice.action_post()

        self.assertEqual(len(invoice.due_line_ids), 1)
        self.assertEqual(invoice.due_line_ids[0].debit, 230)
        self.assertEqual(
            invoice.due_line_ids[0].account_id,
            self.company_data["default_account_receivable"],
        )
        self.assertEqual(len(invoice.payment_move_line_ids), 0)

        # register payment
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        payment = Form(self.env["account.payment.register"].with_context(**ctx))
        payment_register = payment.save()
        payment_register.action_create_payments()

        self.assertEqual(len(invoice.payment_move_line_ids), 1)
        self.assertEqual(invoice.payment_move_line_ids[0].credit, 230)
        self.assertEqual(
            invoice.payment_move_line_ids[0].account_id,
            self.company_data["default_account_receivable"],
        )

    def test_02_payable(self):
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
            )
        )
        invoice_form.partner_id = self.partner_a
        invoice_form.ref = "Test l10n_br_account_due_list"
        invoice_form.invoice_date = fields.Date.today()
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.price_unit = 100.0
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax_purchase_a)
        invoice = invoice_form.save()
        invoice.action_post()

        self.assertEqual(len(invoice.due_line_ids), 1)
        self.assertEqual(invoice.due_line_ids[0].credit, 115)
        self.assertEqual(
            invoice.due_line_ids[0].account_id,
            self.company_data["default_account_payable"],
        )
        self.assertEqual(len(invoice.payment_move_line_ids), 0)

        # register payment
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        payment = Form(self.env["account.payment.register"].with_context(**ctx))
        payment_register = payment.save()
        payment_register.action_create_payments()

        self.assertEqual(len(invoice.payment_move_line_ids), 1)
        self.assertEqual(invoice.payment_move_line_ids[0].debit, 115)
        self.assertEqual(
            invoice.payment_move_line_ids[0].account_id,
            self.company_data["default_account_payable"],
        )
