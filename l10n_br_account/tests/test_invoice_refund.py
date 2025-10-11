# Copyright (C) 2021  Ygor Carvalho - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestInvoiceRefund(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Refund Sales - (test)",
                account_type="income",
            )
        )

        cls.refund_journal = cls.env["account.journal"].create(
            dict(
                name="Refund Journal - (test)",
                code="TREJ",
                type="sale",
                refund_sequence=True,
                default_account_id=cls.sale_account.id,
            )
        )

        cls.reverse_vals = {
            "date": fields.Date.from_string("2019-02-01"),
            "reason": "no reason",
            "refund_method": "refund",
            "journal_id": cls.refund_journal.id,
        }

        cls.invoice = cls._create_test_invoice("Test Refund Invoice", "Refund Test")

    @classmethod
    def _create_test_invoice(cls, name, line_name):
        """Helper method to create a test invoice with standard configuration"""
        return cls.env["account.move"].create(
            dict(
                name=name,
                move_type="out_invoice",
                invoice_payment_term_id=cls.env.ref(
                    "account.account_payment_term_advance"
                ).id,
                partner_id=cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                journal_id=cls.refund_journal.id,
                document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
                document_serie_id=cls.empresa_lc_document_55_serie_1.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_6").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": cls.env["account.account"]
                            .search(
                                [
                                    (
                                        "account_type",
                                        "=",
                                        "income",
                                    ),
                                    (
                                        "company_id",
                                        "=",
                                        cls.env.company.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": line_name,
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            )
        )

    def _create_fiscal_operation(self, name, code, has_journal=False):
        """Helper method to create a fiscal operation for testing"""
        vals = {
            "name": name,
            "code": code,
            "fiscal_operation_type": "out",
            "fiscal_type": "sale",
        }
        if has_journal:
            vals["journal_id"] = self.refund_journal.id
        return self.env["l10n_br_fiscal.operation"].create(vals)

    def _create_move_reversal(
        self, invoice, force_fiscal_operation_id=None, journal_id=None
    ):
        """Helper method to create AccountMoveReversal with proper context"""
        invoice.action_post()
        vals = {}
        if journal_id:
            vals["journal_id"] = journal_id
        if force_fiscal_operation_id:
            vals["force_fiscal_operation_id"] = force_fiscal_operation_id.id

        return (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(vals)
        )

    def test_refund(self):
        reverse_vals = self.reverse_vals

        invoice = self.invoice
        self.assertEqual(
            invoice.state,
            "draft",
            "Invoice should be in state Draft",
        )

        invoice.action_post()
        self.assertEqual(
            invoice.state,
            "posted",
            "Invoice should be in state Posted",
        )

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(reverse_vals)
        )

        with self.assertRaises(UserError):
            move_reversal.reverse_moves()

        invoice.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")

        with self.assertRaises(UserError):
            move_reversal.reverse_moves()

        invoice.invoice_line_ids.write(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": (
                    self.env.ref("l10n_br_fiscal.fo_venda_venda").id,
                ),
            }
        )

        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])

        self.assertTrue(reverse_move)

        self.assertEqual(
            reverse_move.operation_name,
            "Devolução de Venda",
            "The refund process was unsuccessful.",
        )

    def test_refund_force_fiscal_operation(self):
        reverse_vals = self.reverse_vals
        invoice = self.invoice

        invoice.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        invoice.invoice_line_ids.write(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
            }
        )

        invoice.action_post()
        self.assertEqual(
            invoice.state,
            "posted",
            "Invoice should be in state Posted",
        )

        reverse_vals.update(
            {
                "force_fiscal_operation_id": self.env.ref(
                    "l10n_br_fiscal.fo_simples_remessa"
                ).id
            }
        )
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(reverse_vals)
        )

        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])

        self.assertTrue(reverse_move)

        self.assertEqual(
            reverse_move.operation_name,
            "Simples Remessa",
            "The force fiscal operation process was unsuccessful.",
        )

    def test_compute_journal_id_with_force_fiscal_operation_journal(self):
        """Test _compute_journal_id when force_fiscal_operation has journal_id"""
        fiscal_operation = self._create_fiscal_operation(
            "Test Operation with Journal", "TEST_OP", has_journal=True
        )

        # Create a different journal to test the override
        different_journal = self.env["account.journal"].create(
            {
                "name": "Different Journal - (test)",
                "code": "DIFF",
                "type": "sale",
                "default_account_id": self.sale_account.id,
            }
        )

        invoice = self._create_test_invoice("Test Refund Invoice 2", "Refund Test 2")
        move_reversal = self._create_move_reversal(
            invoice,
            force_fiscal_operation_id=fiscal_operation,
            journal_id=different_journal.id,
        )

        # Store original journal_id
        original_journal_id = move_reversal.journal_id.id

        move_reversal._compute_journal_id()

        # Should be overridden by force_fiscal_operation_id.journal_id
        self.assertEqual(
            move_reversal.journal_id.id,
            self.refund_journal.id,
            "Journal ID should be set from force_fiscal_operation_id.journal_id",
        )
        self.assertNotEqual(
            move_reversal.journal_id.id,
            original_journal_id,
            "Journal ID should be overridden by force_fiscal_operation_id.journal_id",
        )

    def test_compute_journal_id_without_force_fiscal_operation_journal(self):
        """Test _compute_journal_id when force_fiscal_operation has no journal_id"""
        fiscal_operation = self._create_fiscal_operation(
            "Test Operation without Journal", "TEST_OP_NO_JOURNAL", has_journal=False
        )

        invoice = self._create_test_invoice("Test Refund Invoice 3", "Refund Test 3")
        move_reversal = self._create_move_reversal(
            invoice,
            force_fiscal_operation_id=fiscal_operation,
            journal_id=self.refund_journal.id,
        )

        # Store original journal_id
        original_journal_id = move_reversal.journal_id.id

        move_reversal._compute_journal_id()

        # Should remain unchanged since force_fiscal_operation has no journal_id
        self.assertEqual(
            move_reversal.journal_id.id,
            original_journal_id,
            "Journal ID should remain unchanged when force_fiscal_operation\
                has no journal_id",
        )

    def test_compute_journal_id_without_force_fiscal_operation_id(self):
        """Test _compute_journal_id when force_fiscal_operation_id is not set"""
        invoice = self._create_test_invoice("Test Refund Invoice 4", "Refund Test 4")
        move_reversal = self._create_move_reversal(
            invoice, journal_id=self.refund_journal.id
        )

        # Store original journal_id
        original_journal_id = move_reversal.journal_id.id

        move_reversal._compute_journal_id()

        # Should remain unchanged since there's no force_fiscal_operation_id
        self.assertEqual(
            move_reversal.journal_id.id,
            original_journal_id,
            "Journal ID should remain unchanged when force_fiscal_operation_id\
                 is not set",
        )
