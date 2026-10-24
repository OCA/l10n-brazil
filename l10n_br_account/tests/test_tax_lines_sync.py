# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestTaxLinesSync(AccountMoveBRCommon):
    """Editing a move must update its tax lines, not shuffle them.

    The key of the needed tax lines has to match the ``tax_key`` of the existing
    ones. When it does not, the dynamic lines sync deletes and recreates every
    tax line, and reuses the deleted ones by writing the new values on them in
    whatever order they come, so a line can take the account and the label of
    another one (see l10n_br_account_withholding, test_tax_lines_sync).
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")

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
            document_number="4997",
        )

    def test_needed_tax_keys_match_existing_tax_keys(self):
        move = self._purchase_move()
        tax_lines = move.line_ids.filtered(lambda line: line.display_type == "tax")
        self.assertTrue(tax_lines, "the purchase move has tax lines")
        existing = {line.tax_key for line in tax_lines}
        product_line = move.invoice_line_ids.filtered("product_id")[:1]
        needed = {
            key
            for key in product_line.compute_all_tax
            if key.get("tax_repartition_line_id")
        }
        self.assertTrue(needed, "the product line computes tax lines")
        self.assertEqual(needed, existing)
