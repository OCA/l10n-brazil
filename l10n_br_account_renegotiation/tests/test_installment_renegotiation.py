from datetime import date, timedelta
from unittest.mock import patch

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

        # Create Payment Methods and Modes (Dependencies of account_payment_partner)
        cls.payment_method = cls.env["account.payment.method"].create(
            {
                "name": "Boleto",
                "code": "boleto",
                "payment_type": "inbound",
            }
        )
        cls.payment_method_pix = cls.env["account.payment.method"].create(
            {
                "name": "PIX",
                "code": "pix",
                "payment_type": "inbound",
            }
        )

        cls.payment_mode_1 = cls.env["account.payment.mode"].create(
            {
                "name": "Boleto Banco A",
                "payment_method_id": cls.payment_method.id,
                "company_id": cls.company.id,
                "bank_account_link": "variable",
            }
        )
        cls.payment_mode_2 = cls.env["account.payment.mode"].create(
            {
                "name": "PIX Banco B",
                "payment_method_id": cls.payment_method_pix.id,
                "company_id": cls.company.id,
                "bank_account_link": "variable",
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
                "payment_mode_id": self.payment_mode_1.id,  # Default to Mode 1
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

    def test_heterogeneous_payment_modes(self):
        """Test that different payment modes can be set for different installments."""
        invoice = self._create_posted_invoice(1000.0)

        # Initial check: all lines should have Mode 1
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertTrue(
            all(line.payment_mode_id == self.payment_mode_1 for line in term_lines)
        )

        # Open Wizard
        wizard = (
            self.env["account.installment.renegotiation.wizard"]
            .with_user(self.account_manager)
            .create({"move_id": invoice.id})
        )

        # Sort lines by date to be deterministic
        lines = wizard.line_ids.sorted("date_maturity")
        self.assertEqual(len(lines), 3)

        # Change the payment mode of the last installment to Mode 2 (PIX)
        # Keep the others as Mode 1 (Boleto)
        lines[2].payment_mode_id = self.payment_mode_2

        wizard.action_apply()

        # Check results on the invoice
        new_term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")

        self.assertEqual(len(new_term_lines), 3)
        self.assertEqual(new_term_lines[0].payment_mode_id, self.payment_mode_1)
        self.assertEqual(new_term_lines[1].payment_mode_id, self.payment_mode_1)
        self.assertEqual(new_term_lines[2].payment_mode_id, self.payment_mode_2)

    def test_cnab_lifecycle_hooks(self):
        """Test that CNAB hooks (Baixa and Inclusao) are called if they exist."""
        # Conditionally skip the test if the CNAB module is not installed in the DB
        if not hasattr(self.env["account.move"], "load_cnab_info"):
            self.skipTest(
                "Module l10n_br_account_payment_order is not installed. "
                "Skipping CNAB lifecycle test."
            )

        invoice = self._create_posted_invoice(1000.0)

        # Flags to verify calls
        hooks_called = {"baixa": False, "inclusao": False}

        def mock_cnab_already_start(self):
            # Simulate that the Boleto was already sent to bank
            return True

        def mock_update_cnab_for_cancel_invoice(self):
            # Simulate the Baixa request
            hooks_called["baixa"] = True

        def mock_load_cnab_info(self):
            # Simulate generating new Nosso Numero (Inclusao)
            hooks_called["inclusao"] = True

        # Patch the active registry class
        AccountMoveModel = type(self.env["account.move"])
        AccountMoveLineModel = type(self.env["account.move.line"])

        with patch.object(
            AccountMoveLineModel, "_cnab_already_start", mock_cnab_already_start
        ), patch.object(
            AccountMoveLineModel,
            "update_cnab_for_cancel_invoice",
            mock_update_cnab_for_cancel_invoice,
        ), patch.object(AccountMoveModel, "load_cnab_info", mock_load_cnab_info):
            # Run renegotiation
            wizard = (
                self.env["account.installment.renegotiation.wizard"]
                .with_user(self.account_manager)
                .create({"move_id": invoice.id})
            )

            # Just change a date to trigger logic
            wizard.line_ids[0].date_maturity = date.today() + timedelta(days=99)

            wizard.action_apply()

        # Assertions
        self.assertTrue(
            hooks_called["baixa"],
            "The wizard should call update_cnab_for_cancel_invoice() on old lines "
            "if _cnab_already_start() returns True.",
        )
        self.assertTrue(
            hooks_called["inclusao"],
            "The wizard should call load_cnab_info() on the move after creating "
            "new lines.",
        )

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
