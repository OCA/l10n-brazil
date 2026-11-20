# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCTeVTotDFe(TransactionCase):
    """Totals of the CT-e under NT CT-e 2026.004.

    From 2027 on (by the issue date, dhEmi) IBS and CBS are part of vTPrest
    and vTotDFe repeats vTPrest (rule 365), so IBS and CBS are never added
    twice. In 2026 vTPrest has no IBS/CBS. vTPrestLiq is vTPrest without them.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="America/Sao_Paulo")
        )
        cls.cte = cls.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")
        cls.line = cls.cte.fiscal_line_ids[0]
        cls.line.price_unit = 1000.0
        cls.ibs_value = 1.0
        cls.cbs_value = 9.0
        cls.ibs_cbs_value = cls.ibs_value + cls.cbs_value

    def _set_ibs_cbs(self, included_in_total=False):
        """Write IBS/CBS on the line. With included_in_total the tax groups
        add them to fiscal_amount_total, as a fiscal engine that treats them
        as not included in the price would do."""
        ibs_tax = self.env.ref("l10n_br_fiscal.tax_ibs_0_1")
        cbs_tax = self.env.ref("l10n_br_fiscal.tax_cbs_0_9")
        (
            ibs_tax.tax_group_id | cbs_tax.tax_group_id
        ).tax_include = not included_in_total
        self.line.write({"ibs_tax_id": ibs_tax.id, "cbs_tax_id": cbs_tax.id})
        self.line.flush_recordset()
        vals = {"ibs_value": self.ibs_value, "cbs_value": self.cbs_value}
        if included_in_total:
            vals["amount_tax_not_included"] = (
                self.line.amount_tax_not_included + self.ibs_cbs_value
            )
        self.line.write(vals)

    def _set_issue_date(self, utc_datetime):
        self.cte.document_date = datetime.strptime(utc_datetime, "%Y-%m-%d %H:%M:%S")

    def _assert_totals(self, net, total):
        cte = self.cte
        self.assertAlmostEqual(cte.cte40_vTPrestLiq, net, places=2)
        self.assertAlmostEqual(cte.cte40_vTPrest, total, places=2)
        self.assertAlmostEqual(cte.cte40_vTotDFe, cte.cte40_vTPrest, places=2)

    @freeze_time("2027-03-01 12:00:00")
    def test_2026_issue_date_without_ibs_cbs_in_vtprest(self):
        """CT-e issued in 2026, processed with the clock in 2027."""
        self._set_ibs_cbs()
        self._set_issue_date("2026-12-31 15:00:00")
        net = self.cte.fiscal_amount_total
        self.assertAlmostEqual(
            self.cte.cte40_vIBS + self.cte.cte40_vCBS, self.ibs_cbs_value, places=2
        )
        self._assert_totals(net, net)

    @freeze_time("2026-10-13 12:00:00")
    def test_2027_issue_date_ibs_cbs_in_vtprest_once(self):
        """CT-e issued in 2027, processed with the clock in 2026."""
        self._set_ibs_cbs()
        self._set_issue_date("2027-01-01 15:00:00")
        net = self.cte.fiscal_amount_total
        self._assert_totals(net, net + self.ibs_cbs_value)

    @freeze_time("2027-01-01 01:00:00")
    def test_issue_date_uses_local_timezone(self):
        """22h of 31/12/2026 in Sao Paulo is 01:00 of 01/01/2027 in UTC:
        the 2026 rule applies, as the dhEmi says."""
        self._set_ibs_cbs()
        self._set_issue_date("2027-01-01 01:00:00")
        net = self.cte.fiscal_amount_total
        self._assert_totals(net, net)
        # one hour later it is 2027 in Sao Paulo too
        self._set_issue_date("2027-01-01 03:00:00")
        self._assert_totals(net, net + self.ibs_cbs_value)

    def test_2027_ibs_cbs_already_in_amount_total(self):
        """IBS/CBS already added to fiscal_amount_total are not added again."""
        self._set_ibs_cbs(included_in_total=True)
        self._set_issue_date("2027-02-01 12:00:00")
        total = self.cte.fiscal_amount_total
        self._assert_totals(total - self.ibs_cbs_value, total)
        # in 2026 they stay out of vTPrest
        self._set_issue_date("2026-11-20 12:00:00")
        self._assert_totals(total - self.ibs_cbs_value, total - self.ibs_cbs_value)

    def test_without_ibs_cbs(self):
        """Without IBS/CBS vTotDFe is not informed and vTPrest is the net."""
        self.line.write(
            {"ibs_value": 0.0, "cbs_value": 0.0, "ibs_percent": 0.0, "cbs_percent": 0.0}
        )
        self._set_issue_date("2027-02-01 12:00:00")
        net = self.cte.fiscal_amount_total
        self.assertAlmostEqual(self.cte.cte40_vTPrest, net, places=2)
        self.assertAlmostEqual(self.cte.cte40_vTPrestLiq, net, places=2)
        self.assertFalse(self.cte.cte40_vTotDFe)
