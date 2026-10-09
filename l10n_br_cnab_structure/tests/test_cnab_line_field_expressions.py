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
