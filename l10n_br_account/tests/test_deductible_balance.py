# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestDeductibleBalance(AccountMoveBRCommon):
    """The balance of a move cannot follow the company in the environment.

    `deductible_taxes` is company dependent, and `_sync_invoice` reads it to
    decide whether the product line takes the full document total or the total
    minus the taxes. Reading it in the environment company instead of the
    company of the line makes the same move balance differently depending on
    which company the user happens to have selected on screen.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.other_company = cls.env["res.company"].create(
            {"name": "Empresa que nao deduz"}
        )
        cls.env.user.company_ids += cls.other_company
        # Deducts in the company of the invoice, does not deduct in the other.
        cls.operation.with_company(cls.env.company).deductible_taxes = True
        cls.operation.with_company(cls.other_company).deductible_taxes = False

    def _purchase_move(self):
        return self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.operation,
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="4996",
        )

    def _product_line(self, move):
        return move.invoice_line_ids.filtered(lambda line: line.product_id)[:1]

    def test_the_flag_is_read_per_company(self):
        """Guard of the scenario: the two companies really disagree.

        Without this the next test could pass for the wrong reason, with both
        readings landing on the same value.
        """
        self.assertTrue(self.operation.with_company(self.env.company).deductible_taxes)
        self.assertFalse(
            self.operation.with_company(self.other_company).deductible_taxes
        )

    def test_the_balance_does_not_follow_the_environment_company(self):
        """Re-syncing from another company must not move the balance."""
        move = self._purchase_move()
        line = self._product_line(move)
        self.assertTrue(line, "the purchase move has a product line")
        before = line.balance

        # Touch the line from an environment sitting on the other company, so
        # `_sync_invoice` runs again there. Both companies stay allowed, which
        # is the real scenario: one user, two companies, and the selector on
        # the wrong one. `with_company` alone would drop the company of the
        # line from `allowed_company_ids` and the record rule would make
        # it unreadable, which is a different failure.
        other_env = line.with_context(
            allowed_company_ids=[self.other_company.id, self.env.company.id]
        )
        self.assertEqual(other_env.env.company, self.other_company)
        other_env.write({"quantity": line.quantity})

        self.assertEqual(
            line.balance,
            before,
            "the balance followed the company in the environment",
        )
