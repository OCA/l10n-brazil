# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestRevenueCode(TransactionCase):
    """The revenue code table is the authority's, and it carries the rules."""

    def _code(self, xmlid):
        return self.env.ref("l10n_br_dctfweb.%s" % xmlid)

    def test_the_whole_table_is_loaded(self):
        """The manual publishes 240 codes: all of them have to be there."""
        codes = self.env["l10n_br_dctfweb.revenue.code"].search([])
        self.assertEqual(len(codes), 240)

    def test_mit_code_is_the_six_digits_the_layout_writes(self):
        code = self._code("revenue_code_022012")
        self.assertEqual(code.code, "0220")
        self.assertEqual(code.extension, "12")
        self.assertEqual(code.mit_code, "022012")

    def test_ipi_debit_needs_the_establishment(self):
        code = self.env["l10n_br_dctfweb.revenue.code"].search(
            [("group", "=", "ipi")], limit=1
        )
        self.assertTrue(code.requires_establishment)

    def test_other_contributions_needs_the_establishment_except_one_code(self):
        """Manual, item 4.2, I: every code but 9197-01."""
        exception = self._code("revenue_code_919701")
        self.assertEqual(exception.group, "other_contributions")
        self.assertFalse(exception.requires_establishment)
        other = self.env["l10n_br_dctfweb.revenue.code"].search(
            [("group", "=", "other_contributions"), ("mit_code", "!=", "919701")],
            limit=1,
        )
        self.assertTrue(other.requires_establishment)

    def test_ret_needs_the_incorporation_except_one_code(self):
        """Manual, item 4.2, II: every code but 6177-01."""
        exception = self._code("revenue_code_617701")
        self.assertEqual(exception.group, "ret")
        self.assertFalse(exception.requires_incorporation)
        other = self.env["l10n_br_dctfweb.revenue.code"].search(
            [("group", "=", "ret"), ("mit_code", "!=", "617701")], limit=1
        )
        self.assertTrue(other.requires_incorporation)

    def test_only_the_gold_code_needs_the_city(self):
        """Manual, item 4.2, IV: revenue code 4028-02."""
        gold = self._code("revenue_code_402802")
        self.assertTrue(gold.requires_gold_city)
        self.assertEqual(
            self.env["l10n_br_dctfweb.revenue.code"].search_count(
                [("requires_gold_city", "=", True)]
            ),
            1,
        )

    def test_extension_ten_is_a_postponed_debit(self):
        postponed = self._code("revenue_code_022010")
        self.assertTrue(postponed.is_postponed)
        self.assertFalse(postponed.requires_debit_year)

    def test_annual_irpj_needs_the_debit_year(self):
        """Layout, AnoDebito: annual code whose extension is not 10."""
        annual = self._code("revenue_code_243001")
        self.assertEqual(annual.periodicity, "annual")
        self.assertTrue(annual.requires_debit_year)
        self.assertFalse(annual.is_postponed)

    def test_a_daily_or_ten_day_code_needs_the_period(self):
        ten_day = self._code("revenue_code_402802")
        self.assertEqual(ten_day.periodicity, "ten_day")
        self.assertTrue(ten_day.requires_period)
        monthly = self._code("revenue_code_919701")
        self.assertEqual(monthly.periodicity, "monthly")
        self.assertFalse(monthly.requires_period)

    def test_a_joint_venture_code_accepts_the_scp_cnpj(self):
        """The table marks the joint venture codes in the description."""
        scp = self._code("revenue_code_022008")
        self.assertIn("SCP", scp.name.upper())
        self.assertTrue(scp.allows_scp)
        plain = self._code("revenue_code_022001")
        self.assertFalse(plain.allows_scp)

    def test_a_code_outside_the_scp_groups_never_takes_the_scp_cnpj(self):
        """Manual, item 4.2, III: only IRPJ, CSLL, PIS and COFINS."""
        codes = self.env["l10n_br_dctfweb.revenue.code"].search(
            [("allows_scp", "=", True)]
        )
        self.assertTrue(codes)
        self.assertFalse(
            codes.filtered(
                lambda c: c.group not in ("irpj", "csll", "pis_pasep", "cofins")
            )
        )

    def test_a_malformed_code_is_refused(self):
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dctfweb.revenue.code"].create(
                {
                    "code": "220",
                    "extension": "01",
                    "name": "Wrong",
                    "group": "irpj",
                    "periodicity": "monthly",
                }
            )

    def test_the_same_code_cannot_be_registered_twice(self):
        from psycopg2 import IntegrityError

        from odoo.tools import mute_logger

        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.env["l10n_br_dctfweb.revenue.code"].create(
                {
                    "code": "0220",
                    "extension": "01",
                    "name": "Duplicated",
                    "group": "irpj",
                    "periodicity": "quarterly",
                }
            )
            self.env.flush_all()
