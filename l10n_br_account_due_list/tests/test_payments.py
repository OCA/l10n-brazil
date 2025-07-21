# Copyright (C) 2021 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.tests import Form, common


class TestPayments(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "Test receivable account",
                "code": "ACCRV",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.account_payable = cls.env["account.account"].create(
            {
                "name": "Test payable account",
                "code": "ACCPAY",
                "account_type": "liability_payable",
                "reconcile": True,
            }
        )
        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo",
                "property_account_receivable_id": cls.account_receivable.id,
                "property_account_payable_id": cls.account_payable.id,
            }
        )
        cls.tax1 = cls.env["account.tax"].create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "amount": 15.0,
                "price_include": True,
            }
        )
        cls.tax2 = cls.env["account.tax"].create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "amount": 15.0,
                "price_include": True,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test purchase journal", "code": "TPUR", "type": "purchase"}
        )
        cls.invoice_line = cls.env["account.move.line"]

    def test_01_receivable(self):
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        invoice_form.partner_id = self.partner_1
        invoice_form.ref = "Test l10n_br_account_due_list"
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.price_unit = 200.0
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax1)
        invoice = invoice_form.save()
        invoice.action_post()  # Use action_post() instead of _post() in tests

        self.assertEqual(len(invoice.due_line_ids), 1)
        self.assertEqual(invoice.due_line_ids[0].debit, 200)
        self.assertEqual(invoice.due_line_ids[0].account_id, self.account_receivable)
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
        self.assertEqual(invoice.payment_move_line_ids[0].credit, 200)
        self.assertEqual(
            invoice.payment_move_line_ids[0].account_id, self.account_receivable
        )

    def test_02_payable(self):
        invoice_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
            )
        )
        invoice_form.partner_id = self.partner_1
        invoice_form.ref = "Test l10n_br_account_due_list"
        invoice_form.invoice_date = fields.Date.today()
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.price_unit = 100.0
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax2)
        invoice = invoice_form.save()
        invoice.action_post()  # Use action_post() instead of _post() in tests

        self.assertEqual(len(invoice.due_line_ids), 1)
        self.assertEqual(invoice.due_line_ids[0].credit, 100)
        self.assertEqual(invoice.due_line_ids[0].account_id, self.account_payable)
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
        self.assertEqual(invoice.payment_move_line_ids[0].debit, 100)
        self.assertEqual(
            invoice.payment_move_line_ids[0].account_id, self.account_payable
        )
