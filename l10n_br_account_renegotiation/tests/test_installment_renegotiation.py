# Copyright 2026 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInstallmentRenegotiation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create a company
        cls.company = cls.env.ref("base.main_company")

        # Get or create a customer
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "company_id": cls.company.id,
            }
        )

        # Get receivable account
        cls.account_receivable = cls.env["account.account"].search(
            [
                ("account_type", "=", "asset_receivable"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )

        # Get income account
        cls.account_income = cls.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )

        # Create a product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "service",
                "list_price": 1000.0,
            }
        )

        # Create a payment term with 3 installments
        # In Odoo 16, payment term lines use 'days' (not 'nb_days')
        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "3 Installments Test",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 33.33,
                            "days": 30,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 33.33,
                            "days": 60,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 90,
                        },
                    ),
                ],
            }
        )

        # Get user with account manager rights
        cls.account_manager = cls.env.ref("base.user_admin")

    def _create_posted_invoice(self, amount=1000.0):
        """Create and post an invoice with the 3-installment payment term."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line",
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": self.account_income.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_can_renegotiate_installments_posted_invoice(self):
        """Test that can_renegotiate_installments is True for posted invoice."""
        invoice = self._create_posted_invoice()
        self.assertTrue(invoice.can_renegotiate_installments)

    def test_cannot_renegotiate_draft_invoice(self):
        """Test that can_renegotiate_installments is False for draft invoice."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line",
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "account_id": self.account_income.id,
                        },
                    )
                ],
            }
        )
        self.assertFalse(invoice.can_renegotiate_installments)

    def test_action_opens_wizard(self):
        """Test that action_renegotiate_installments opens the wizard."""
        invoice = self._create_posted_invoice()

        # Execute as account manager
        result = invoice.with_user(
            self.account_manager
        ).action_renegotiate_installments()

        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(
            result["res_model"], "account.installment.renegotiation.wizard"
        )
        self.assertEqual(result["target"], "new")

        # Check wizard was created with correct data
        wizard = self.env["account.installment.renegotiation.wizard"].browse(
            result["res_id"]
        )
        self.assertEqual(wizard.move_id, invoice)

        # Check lines were populated
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(len(wizard.line_ids), len(payment_term_lines))

    def test_wizard_validates_total_unchanged(self):
        """Test that wizard prevents changing total amount."""
        invoice = self._create_posted_invoice()

        wizard = self.env["account.installment.renegotiation.wizard"].create(
            {
                "move_id": invoice.id,
            }
        )

        # Modify amounts to change total
        for line in wizard.line_ids:
            line.amount = line.amount + 100  # Increase each by 100

        # Should raise error when applying
        with self.assertRaises(UserError):
            wizard.with_user(self.account_manager).action_apply()

    def test_wizard_allows_date_change(self):
        """Test that wizard allows changing due dates while keeping total."""
        invoice = self._create_posted_invoice()

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        # Store original dates
        wizard.line_ids.mapped("date_maturity")

        # Change dates
        new_date = date.today() + timedelta(days=180)
        for line in wizard.line_ids:
            line.date_maturity = new_date

        # Apply should succeed
        wizard.action_apply()

        # Check dates were updated
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        for line in payment_term_lines:
            self.assertEqual(line.date_maturity, new_date)

    def test_wizard_allows_amount_redistribution(self):
        """Test that wizard allows redistributing amounts while keeping total."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        # Get total
        total = sum(wizard.line_ids.mapped("amount"))

        # Redistribute: 50% on first, 25% on each of the remaining
        lines = wizard.line_ids.sorted("date_maturity")
        if len(lines) >= 3:
            lines[0].amount = total / 2
            lines[1].amount = total / 4
            lines[2].amount = total / 4
        elif len(lines) == 2:
            lines[0].amount = total / 2
            lines[1].amount = total / 2

        # Apply should succeed
        wizard.action_apply()

        # Check amounts were updated
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        new_total = sum(abs(line.amount_currency) for line in payment_term_lines)
        self.assertAlmostEqual(new_total, total, places=2)

    def test_chatter_message_posted(self):
        """Test that a message is posted to chatter after renegotiation."""
        invoice = self._create_posted_invoice()

        initial_message_count = len(invoice.message_ids)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        # Change a date
        wizard.line_ids[0].date_maturity = date.today() + timedelta(days=365)

        wizard.action_apply()

        # Check new message was posted
        self.assertGreater(len(invoice.message_ids), initial_message_count)

        # Check message content mentions renegotiation
        latest_message = invoice.message_ids[0]
        self.assertIn("Renegotiated", latest_message.body)

    def test_invoice_state_unchanged(self):
        """Test that invoice state remains 'posted' after renegotiation."""
        invoice = self._create_posted_invoice()
        self.assertEqual(invoice.state, "posted")

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        # Change a date
        wizard.line_ids[0].date_maturity = date.today() + timedelta(days=365)

        wizard.action_apply()

        # State should still be posted
        self.assertEqual(invoice.state, "posted")

    def test_cannot_renegotiate_reconciled_lines(self):
        """Test that fully reconciled invoices cannot be renegotiated."""
        invoice = self._create_posted_invoice(100.0)

        # Register payment for full amount
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
                "amount": 100.0,
                "currency_id": invoice.currency_id.id,
            }
        )
        payment.action_post()

        # Reconcile
        lines = (invoice + payment.move_id).line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
            and not line.reconciled
        )
        if lines:
            lines.reconcile()

        # After full reconciliation, should not be able to renegotiate
        invoice.invalidate_recordset()
        self.assertFalse(invoice.can_renegotiate_installments)

    def test_add_installment(self):
        """Test adding a new installment line."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        original_count = len(wizard.line_ids)
        sum(wizard.line_ids.mapped("amount"))

        # Redistribute to add a new line
        # Reduce each existing by some amount and add a new one
        reduction = 100.0
        for line in wizard.line_ids:
            line.amount = line.amount - reduction

        # Add new line
        self.env["account.installment.renegotiation.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date_maturity": date.today() + timedelta(days=120),
                "amount": reduction * original_count,
            }
        )

        # Apply
        wizard.action_apply()

        # Check we now have more payment_term lines
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(len(payment_term_lines), original_count + 1)

    def test_remove_installment(self):
        """Test removing an installment line."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": invoice.id,
                }
            )
        )

        original_count = len(wizard.line_ids)
        self.assertGreaterEqual(
            original_count, 2, "Need at least 2 lines to test removal"
        )

        # Get total and remove one line, redistributing its amount
        sum(wizard.line_ids.mapped("amount"))
        line_to_remove = wizard.line_ids[-1]
        amount_to_redistribute = line_to_remove.amount

        # Remove line
        line_to_remove.unlink()

        # Redistribute amount to remaining lines
        remaining_lines = wizard.line_ids
        extra_per_line = amount_to_redistribute / len(remaining_lines)
        for line in remaining_lines:
            line.amount = line.amount + extra_per_line

        # Apply
        wizard.action_apply()

        # Check we now have fewer payment_term lines
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(len(payment_term_lines), original_count - 1)
