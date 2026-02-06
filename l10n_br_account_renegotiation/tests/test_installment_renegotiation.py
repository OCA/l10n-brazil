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
        """Test that draft invoices cannot be renegotiated."""
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

        # Also test that action raises error
        with self.assertRaises(UserError):
            invoice.with_user(self.account_manager).action_renegotiate_installments()

    def test_wizard_validates_posted_state(self):
        """Test wizard validation when invoice is reset to draft."""
        invoice = self._create_posted_invoice()

        # Create wizard while invoice is posted
        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Reset invoice to draft
        invoice.button_draft()

        # Wizard should reject because invoice is no longer posted
        with self.assertRaises(UserError):
            wizard.action_apply()

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

        # Redistribute: 50% on first, 25% on each of the remaining two
        lines = wizard.line_ids.sorted("date_maturity")
        self.assertEqual(len(lines), 3, "Expected 3 installment lines")
        lines[0].amount = total / 2
        lines[1].amount = total / 4
        lines[2].amount = total / 4

        # Apply should succeed
        wizard.action_apply()

        # Check amounts were updated
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        new_total = sum(abs(line.amount_currency) for line in payment_term_lines)
        self.assertAlmostEqual(new_total, total, places=2)

        # Verify debit/credit correctness:
        # customer invoice receivable lines must be debit
        for line in payment_term_lines:
            self.assertGreater(
                line.debit,
                0,
                "Customer invoice payment_term lines must have debit>0",
            )
            self.assertEqual(
                line.credit,
                0,
                "Customer invoice payment_term lines must have credit=0",
            )
            self.assertGreater(
                line.amount_currency,
                0,
                "Customer invoice payment_term lines must have "
                "positive amount_currency",
            )

        # Verify the move is still balanced (debits == credits)
        total_debit = sum(invoice.line_ids.mapped("debit"))
        total_credit = sum(invoice.line_ids.mapped("credit"))
        self.assertAlmostEqual(
            total_debit,
            total_credit,
            places=2,
            msg="Move must be balanced after renegotiation (debits == credits)",
        )

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
        self.assertTrue(lines, "Expected unreconciled receivable lines")
        lines.reconcile()

        # After full reconciliation, should not be able to renegotiate
        invoice.invalidate_recordset()
        self.assertFalse(invoice.can_renegotiate_installments)

        # Also test that action raises error
        with self.assertRaises(UserError):
            invoice.with_user(self.account_manager).action_renegotiate_installments()

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

    def test_non_manager_cannot_renegotiate(self):
        """Test that users without account manager rights cannot renegotiate."""
        invoice = self._create_posted_invoice()

        # Create a user without account manager rights
        basic_user = self.env["res.users"].create(
            {
                "name": "Basic User",
                "login": "basic_user",
                "groups_id": [
                    (6, 0, [self.env.ref("account.group_account_invoice").id])
                ],
            }
        )

        # Test action validation
        with self.assertRaises(UserError):
            invoice.with_user(basic_user).action_renegotiate_installments()

        # Test wizard validation (defensive check)
        wizard = self.env["account.installment.renegotiation.wizard"].create(
            {"move_id": invoice.id}
        )
        with self.assertRaises(UserError):
            wizard.with_user(basic_user).action_apply()

    def test_cannot_renegotiate_journal_entry(self):
        """Test that journal entries cannot be renegotiated."""
        # Create a journal entry (not an invoice)
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)],
            limit=1,
        ) or self.env["account.journal"].create(
            {
                "name": "Misc Journal",
                "type": "general",
                "code": "MISC",
                "company_id": self.company.id,
            }
        )

        entry = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Debit",
                            "account_id": self.account_receivable.id,
                            "debit": 100,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Credit",
                            "account_id": self.account_income.id,
                            "debit": 0,
                            "credit": 100,
                        },
                    ),
                ],
            }
        )
        entry.action_post()

        # can_renegotiate should be False for journal entries
        self.assertFalse(entry.can_renegotiate_installments)

        # action should raise error
        with self.assertRaises(UserError):
            entry.with_user(self.account_manager).action_renegotiate_installments()

    def test_vendor_bill_renegotiation(self):
        """Test that vendor bills can also be renegotiated."""
        account_expense = self.env["account.account"].search(
            [
                ("account_type", "=", "expense"),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )

        # Create a vendor bill
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Expense",
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "account_id": account_expense.id,
                        },
                    )
                ],
            }
        )
        bill.action_post()

        # Should be able to renegotiate
        self.assertTrue(bill.can_renegotiate_installments)

        # Open wizard and change dates
        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create(
                {
                    "move_id": bill.id,
                }
            )
        )

        new_date = date.today() + timedelta(days=180)
        for line in wizard.line_ids:
            line.date_maturity = new_date

        wizard.action_apply()

        # Verify dates changed
        payment_term_lines = bill.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        for line in payment_term_lines:
            self.assertEqual(line.date_maturity, new_date)

        # Verify debit/credit correctness: vendor bill payable lines must be credit
        for line in payment_term_lines:
            self.assertEqual(
                line.debit,
                0,
                "Vendor bill payment_term lines must have debit=0",
            )
            self.assertGreater(
                line.credit,
                0,
                "Vendor bill payment_term lines must have credit>0",
            )
            self.assertLess(
                line.amount_currency,
                0,
                "Vendor bill payment_term lines must have negative amount_currency",
            )

        # Verify the move is still balanced (debits == credits)
        total_debit = sum(bill.line_ids.mapped("debit"))
        total_credit = sum(bill.line_ids.mapped("credit"))
        self.assertAlmostEqual(
            total_debit,
            total_credit,
            places=2,
            msg="Move must be balanced after renegotiation (debits == credits)",
        )

    def test_wizard_validates_no_lines(self):
        """Test that wizard rejects when all lines are removed."""
        invoice = self._create_posted_invoice()

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Remove all lines
        wizard.line_ids.unlink()

        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_wizard_validates_positive_amounts(self):
        """Test that wizard rejects zero or negative amounts."""
        invoice = self._create_posted_invoice()

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Set one line to zero, redistribute to keep total
        lines = wizard.line_ids.sorted("date_maturity")
        zero_amount = lines[0].amount
        lines[0].amount = 0
        lines[1].amount = lines[1].amount + zero_amount

        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_multi_currency_renegotiation(self):
        """Test renegotiation with invoice in foreign currency."""
        company_currency = self.company.currency_id

        # Pick a foreign currency different from the company's currency
        foreign_currency = self.env["res.currency"].search(
            [("id", "!=", company_currency.id), ("active", "=", True)],
            limit=1,
        )
        if not foreign_currency:
            foreign_currency = self.env["res.currency"].search(
                [("id", "!=", company_currency.id)],
                limit=1,
            )
            foreign_currency.active = True

        # Ensure there is a rate for the foreign currency
        existing_rate = self.env["res.currency.rate"].search(
            [
                ("currency_id", "=", foreign_currency.id),
                ("name", "=", date.today()),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )
        if not existing_rate:
            self.env["res.currency.rate"].create(
                {
                    "currency_id": foreign_currency.id,
                    "name": date.today(),
                    "rate": 5.0,
                    "company_id": self.company.id,
                }
            )

        # Create invoice in foreign currency
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "currency_id": foreign_currency.id,
                "invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line USD",
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "account_id": self.account_income.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()

        # Verify it's multi-currency
        self.assertNotEqual(invoice.currency_id, invoice.company_currency_id)

        # Renegotiate
        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        new_date = date.today() + timedelta(days=180)
        for line in wizard.line_ids:
            line.date_maturity = new_date

        wizard.action_apply()

        # Verify dates changed
        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        for line in payment_term_lines:
            self.assertEqual(line.date_maturity, new_date)

    def test_payment_term_number_after_date_change(self):
        """Test that payment_term_number is updated after renegotiation."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Just change dates
        for idx, line in enumerate(wizard.line_ids.sorted("date_maturity")):
            line.date_maturity = date.today() + timedelta(days=30 * (idx + 1))

        wizard.action_apply()

        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        self.assertEqual(len(payment_term_lines), 3)
        expected = ["1-3", "2-3", "3-3"]
        for line, exp in zip(payment_term_lines, expected, strict=True):
            self.assertEqual(
                line.payment_term_number,
                exp,
                f"Expected payment_term_number '{exp}', "
                f"got '{line.payment_term_number}'",
            )

    def test_payment_term_number_after_add_installment(self):
        """Test payment_term_number is renumbered after adding installment."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Reduce each line by 50 and add a 4th line
        for line in wizard.line_ids:
            line.amount = line.amount - 50.0

        self.env["account.installment.renegotiation.wizard.line"].create(
            {
                "wizard_id": wizard.id,
                "date_maturity": date.today() + timedelta(days=120),
                "amount": 50.0 * len(wizard.line_ids),
            }
        )

        wizard.action_apply()

        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        self.assertEqual(len(payment_term_lines), 4)
        expected = ["1-4", "2-4", "3-4", "4-4"]
        for line, exp in zip(payment_term_lines, expected, strict=True):
            self.assertEqual(
                line.payment_term_number,
                exp,
                f"Expected payment_term_number '{exp}', "
                f"got '{line.payment_term_number}'",
            )

    def test_payment_term_number_after_remove_installment(self):
        """Test payment_term_number is renumbered after removing installment."""
        invoice = self._create_posted_invoice(1000.0)

        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        self.assertEqual(len(wizard.line_ids), 3)

        # Remove last line and redistribute
        lines = wizard.line_ids.sorted("date_maturity")
        removed_amount = lines[-1].amount
        lines[-1].unlink()

        remaining = wizard.line_ids
        extra = removed_amount / len(remaining)
        for line in remaining:
            line.amount = line.amount + extra

        wizard.action_apply()

        payment_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        self.assertEqual(len(payment_term_lines), 2)
        expected = ["1-2", "2-2"]
        for line, exp in zip(payment_term_lines, expected, strict=True):
            self.assertEqual(
                line.payment_term_number,
                exp,
                f"Expected payment_term_number '{exp}', "
                f"got '{line.payment_term_number}'",
            )
