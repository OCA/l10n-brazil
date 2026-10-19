# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCnabLineFieldExpressions(TransactionCase):
    def test_dynamic_content_expressions_compile(self):
        """All dynamic content expressions shipped as data must be valid Python."""
        fields_with_expr = self.env["l10n_br_cnab.line.field"].search(
            [
                "|",
                ("sending_dynamic_content", "!=", False),
                ("return_dynamic_content", "!=", False),
            ]
        )
        self.assertTrue(fields_with_expr)
        for field in fields_with_expr:
            for fname in ("sending_dynamic_content", "return_dynamic_content"):
                expr = field[fname]
                if not expr:
                    continue
                try:
                    compile(expr.strip(), field.display_name, "eval")
                except SyntaxError as e:
                    self.fail(f"Invalid {fname} on {field.display_name}: {e}")

    def test_segment_j_money_fields_keep_cents(self):
        """Discount and payment values of the boleto segment J keep two decimals."""

        class Line:
            discount_value = 10.5
            amount_currency = 1234.56

        cases = {
            "cnab_itau_240_boleto_segmento_j_115_129": "discount_value",
            "cnab_sicoob_240_boleto_segmento_j_100_114": "amount_currency",
            "cnab_sicoob_240_boleto_segmento_j_115_129": "discount_value",
            "cnab_sicoob_240_boleto_segmento_j_153_167": "amount_currency",
        }
        expected = {"discount_value": "1050", "amount_currency": "123456"}
        for xml_id, source in cases.items():
            field = self.env.ref(f"l10n_br_cnab_structure.{xml_id}")
            value = field.output(Line())[1]
            self.assertEqual(len(value), 15, xml_id)
            self.assertEqual(value, expected[source].zfill(15), xml_id)

    def test_itau_segment_j_currency_quantity_is_zeros(self):
        """The currency quantity of the Itau segment J is numeric (zeros)."""
        field = self.env.ref(
            "l10n_br_cnab_structure.cnab_itau_240_boleto_segmento_j_168_182"
        )
        self.assertEqual(field.output(None)[1], "0" * 15)
