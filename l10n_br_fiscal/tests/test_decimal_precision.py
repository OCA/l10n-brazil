# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestDecimalPrecision(TransactionCase):
    def test_quantity_digits(self):
        """The fiscal quantities follow the "Product Unit" decimal precision.

        Odoo 20.0 renamed "Product Unit of Measure" to "Product Unit": an
        unknown name silently falls back to 2 digits.
        """
        self.env.ref("uom.decimal_product_uom").digits = 4
        line_fields = self.env["l10n_br_fiscal.document.line"]._fields
        for fname in ("quantity", "fiscal_quantity"):
            self.assertEqual(line_fields[fname].get_digits(self.env)[1], 4, fname)
