# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Invoice and refund repartition have to stay symmetric.

Core validates that both distributions match, and the Factur-X embedded in the
invoice PDF runs that validation, so a mismatch blocks the PDF download.
"""

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxRepartition(TransactionCase):
    def _tax(self, **vals):
        values = {"name": "Tax test", "amount": 10, "type_tax_use": "sale"}
        values.update(vals)
        return self.env["account.tax"].create(values)

    def _factors(self, tax):
        tax_type = lambda line: line.repartition_type == "tax"  # noqa: E731
        return (
            tax.invoice_repartition_line_ids.filtered(tax_type).mapped(
                "factor_percent"
            ),
            tax.refund_repartition_line_ids.filtered(tax_type).mapped("factor_percent"),
        )

    def _check_core_accepts(self, tax):
        """Core 18.0 also requires the positive tax-repartition factors to sum
        to 100, which a lone -100 line cannot satisfy: the assertion here is the
        symmetry of the invoice and refund distributions, which is what the
        Factur-X validation of the invoice PDF trips on.
        """
        invoice, refund = self._factors(tax)
        self.assertEqual(invoice, refund)

    def test_deductible_without_refund_account(self):
        tax = self._tax(deductible=True)
        tax._update_repartition_lines(False, False)
        invoice, refund = self._factors(tax)
        self.assertEqual(invoice, [-100])
        self.assertEqual(refund, [-100])
        self._check_core_accepts(tax)

    def test_withholdable_without_refund_account(self):
        tax = self._tax(withholdable=True)
        tax._update_repartition_lines(False, False)
        invoice, refund = self._factors(tax)
        self.assertEqual(invoice, refund)
        self.assertEqual(refund, [-100])
        self._check_core_accepts(tax)

    def test_deductible_with_refund_account(self):
        account = self.env["account.account"].create(
            {
                "name": "Tax account",
                "code": "TAXTEST",
                "account_type": "liability_current",
            }
        )
        tax = self._tax(deductible=True)
        tax._update_repartition_lines(account.id, account.id)
        invoice, refund = self._factors(tax)
        self.assertEqual(invoice, [-100])
        self.assertEqual(refund, [-100])
        self._check_core_accepts(tax)

    def test_regular_tax_keeps_positive_factor(self):
        # deductible defaults to True on the mixin, so turn it off explicitly
        tax = self._tax(deductible=False)
        tax._update_repartition_lines(False, False)
        invoice, refund = self._factors(tax)
        self.assertEqual(invoice, [100])
        self.assertEqual(refund, [100])
        tax._validate_repartition_lines()
