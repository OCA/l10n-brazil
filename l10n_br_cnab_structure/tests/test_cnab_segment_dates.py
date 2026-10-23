# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class FakePaymentLine:
    """Minimal stand-in for an account.payment.line read by the CNAB fields."""

    def __init__(self, due_date, pay_date):
        self.ml_maturity_date = due_date
        self.date = pay_date


@tagged("post_install", "-at_install")
class TestCnabSegmentDates(TransactionCase):
    def _output(self, xml_id, line):
        field = self.env.ref(f"l10n_br_cnab_structure.{xml_id}")
        return field.output(line)[1]

    def test_itau_segment_j_dates_and_currency_quantity(self):
        """Itau segment J: due and payment dates of the line, currency quantity
        (168-182) filled with zeros."""
        line = FakePaymentLine(date(2026, 10, 30), date(2026, 10, 28))
        self.assertEqual(
            self._output("cnab_itau_240_boleto_segmento_j_92_99", line), "30102026"
        )
        self.assertEqual(
            self._output("cnab_itau_240_boleto_segmento_j_145_152", line), "28102026"
        )
        self.assertEqual(
            self._output("cnab_itau_240_boleto_segmento_j_168_182", None), "0" * 15
        )
