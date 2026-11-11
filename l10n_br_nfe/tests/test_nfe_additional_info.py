# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestNFeAdditionalInfoControlChars(TransactionCase):
    """The NF-e XSD only accepts characters from space (0x20) upward in
    infAdFisco/infCpl; TABs pasted from spreadsheets must be cleaned."""

    def _export(self, fiscal_text, customer_text):
        doc = self.env["l10n_br_fiscal.document"].new(
            {
                "fiscal_additional_data": fiscal_text,
                "customer_additional_data": customer_text,
            }
        )
        return doc.nfe40_infAdFisco, doc.nfe40_infCpl

    def test_control_chars_removed(self):
        fisco, cpl = self._export(
            "Ref\t123\t\tabc\x0b\x00 end\t",
            "\tCustomer\tA  ,\x1f\x7fB \t C",
        )
        self.assertEqual(fisco, "Ref 123 abc end")
        self.assertEqual(cpl, "Customer A  , B C")
        for value in (fisco, cpl):
            self.assertFalse(
                [c for c in value if ord(c) < 0x20 or ord(c) == 0x7F], value
            )

    def test_line_breaks_unchanged(self):
        fisco, cpl = self._export("line1\nline2\r\nline3", "a\nb")
        self.assertEqual(fisco, "line1line2line3")
        self.assertEqual(cpl, "ab")

    def test_normal_text_unchanged(self):
        text = "Order 10/2026 - Ref.:  ABC (exempt) 1,5%  ok"
        fisco, cpl = self._export(text, text)
        self.assertEqual(fisco, text)
        self.assertEqual(cpl, text)
