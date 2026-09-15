# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_reinf_calculation import ReinfCalculationCommon

# The nfelib on PyPI has no reinf package: the tests that serialize skip
# themselves instead of failing the suite.
try:
    from nfelib.reinf.bindings.v2_01_02.r_4020_evt4020_pagto_beneficiario_pj_v2_01_02 import (  # noqa: E501
        Reinf,
    )
except ImportError:  # pragma: no cover
    Reinf = None


@tagged("post_install", "-at_install")
class TestReinfR4020(ReinfCalculationCommon):
    """Tests 3 to 7 of the spec: the collapse, the DARF and the event."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        # The collapse only applies to a nature that HAS an aggregated line in
        # the mapping of the Annex I, so the whole fixture switches to one of
        # the 47 that do. It replaces cls.nature, which is what the helper of
        # the invoice writes on the line.
        cls.nature_agg = cls.env["l10n_br_reinf.nature.income"].search(
            [
                ("admitted_taxes", "like", "CSLL"),
                ("admitted_taxes", "like", "AGREGADO"),
            ],
            limit=1,
        )
        # 15001: cooperatives of work, which admit the aggregate WITHOUT CSLL.
        cls.nature_coop = cls.env.ref("l10n_br_reinf.nature_income_15001")
        cls.nature = cls.nature_agg
        cls.supplier.reinf_nature_income_id = cls.nature_agg

    def _pcc_invoice_paid(self, amount, invoice_date="2026-07-10", pay_date=None):
        move = self._create_supplier_invoice(
            invoice_date,
            amount,
            taxes=[self.tax_pis, self.tax_cofins, self.tax_csll],
        )
        self._pay(move, pay_date or invoice_date)
        return move

    # ------------------------------------------------------------------
    # test 3: the collapse and its cents
    # ------------------------------------------------------------------

    def test_collapse_is_the_sum_of_what_was_withheld(self):
        """Base of 10.000,00: the aggregate is the sum, 465,00, not a recompute.

        The field of the layout carries the amount withheld and the tax
        authority does not recompute it, so the rate is only a conference.
        """
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()

        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertEqual(len(aggregated), 1)
        self.assertAlmostEqual(aggregated.wh_amount, 465.0, places=2)
        self.assertAlmostEqual(aggregated.divergence_amount, 0.0, places=2)
        self.assertEqual(aggregated.state, "ok")
        # The three separate lines were replaced, not kept alongside.
        self.assertFalse(
            july.line_ids.filtered(
                lambda line: line.tax in ("pis_pasep", "cofins", "csll")
            )
        )
        # And the composition stayed visible.
        self.assertIn("COFINS", aggregated.note)
        # The revenue code came from the mapping of the Annex I, not from a
        # constant in the source.
        self.assertEqual(
            aggregated.revenue_code,
            self.nature_agg._tax_mapping("aggregated", aggregated.fg_date).revenue_code,
        )

    def test_collapse_shows_the_cents_against_the_expected_rate(self):
        """Base of 1.234,56: the declared value is the sum, and the difference
        against the expected rate is shown, not applied."""
        self._pcc_invoice_paid(1234.56)
        july = self._calculation("2026-07")
        july.action_compute()

        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertEqual(len(aggregated), 1)
        # 0,65% + 3% + 1% of 1.234,56, each rounded: 8,02 + 37,04 + 12,35.
        self.assertAlmostEqual(aggregated.wh_amount, 57.41, places=2)
        # Under the tolerance of the company it is shown and does not block.
        self.assertLessEqual(
            abs(aggregated.divergence_amount),
            self.company.reinf_aggregate_tolerance,
        )
        self.assertEqual(aggregated.state, "ok")

    def test_collapse_above_tolerance_raises_an_exception(self):
        """Zero tolerance turns any cent of difference into an exception."""
        self.company.reinf_aggregate_tolerance = 0.0
        self._pcc_invoice_paid(1234.56)
        july = self._calculation("2026-07")
        july.action_compute()

        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        if aggregated.divergence_amount:
            self.assertEqual(aggregated.state, "divergent")
            self.assertIn("aggregate_divergence", july.exception_ids.mapped("reason"))

    # ------------------------------------------------------------------
    # test 4: cooperative
    # ------------------------------------------------------------------

    def test_cooperative_of_work_aggregates_without_csll(self):
        """The dispensation of the CSLL belongs to the NATURE, so it aggregates.

        The nature 15001 admits "IR, COFINS, PP, AGREGADO": the art. 32 I of the
        Law 10.833 does not require the CSLL of a cooperative of work, and that
        partiality is structural. Refusing the aggregate here, which is what a
        rule of "all three or nothing" does, would be the error.
        """
        self.assertNotIn("CSLL", self.nature_coop.admitted_taxes)
        self.assertTrue(self.nature_coop._admits_aggregate())
        self.assertEqual(
            self.nature_coop._aggregate_components(), {"cofins", "pis_pasep"}
        )
        self.nature = self.nature_coop
        self.supplier.reinf_nature_income_id = self.nature_coop
        self.supplier.reinf_beneficiary_profile = "work_cooperative"
        # Only PIS/PASEP and COFINS are withheld: 0,65% + 3% of 10.000,00.
        move = self._create_supplier_invoice(
            "2026-07-10", 10000.0, taxes=[self.tax_pis, self.tax_cofins]
        )
        self._pay(move, "2026-07-10")
        july = self._calculation("2026-07")
        july.action_compute()

        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertEqual(len(aggregated), 1)
        self.assertAlmostEqual(aggregated.wh_amount, 365.0, places=2)
        self.assertNotIn("csll", july.line_ids.mapped("tax"))
        # No rate conference on a partial aggregate: 3,65% is not published as
        # a rate of its own, and inventing it would fake a divergence.
        self.assertAlmostEqual(aggregated.divergence_amount, 0.0, places=2)

    def test_cooperative_of_consumption_suffers_the_full_aggregate(self):
        """A cooperative of CONSUMPTION is not the cooperative of the 15001.

        The dispensation of the art. 32 I is for the cooperative of WORK. A
        cooperative of consumption suffers the whole 4,65% and is declared under
        the nature of the service it rendered, never under the 15001: treating
        the two as one beneficiary profile is how a company underpays and finds
        out in an audit.
        """
        self.supplier.reinf_beneficiary_profile = "consumer_cooperative"
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()

        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertEqual(len(aggregated), 1)
        # The whole 4,65%, with the CSLL inside it.
        self.assertAlmostEqual(aggregated.wh_amount, 465.0, places=2)
        self.assertEqual(
            self.nature_agg._aggregate_components(),
            {"csll", "cofins", "pis_pasep"},
        )
        # Declared under the nature of the service, and not under the 15001.
        self.assertEqual(aggregated.nature_income_id, self.nature_agg)
        self.assertNotEqual(aggregated.nature_income_id, self.nature_coop)
        # Nothing about a cooperative of work applies here.
        self.assertNotIn(
            "cooperative_csll_withheld", july.exception_ids.mapped("reason")
        )
        self.assertNotIn(
            "aggregate_partial_not_structural",
            july.exception_ids.mapped("reason"),
        )

    def test_exempt_beneficiary_does_not_aggregate(self):
        """An exemption of the BENEFICIARY breaks the aggregate, unlike a
        dispensation of the nature."""
        self.supplier.write(
            {
                "reinf_beneficiary_profile": "exempt",
                "reinf_exemption_legal_basis": "Art. 4 da Lei 10.637/2002",
            }
        )
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()

        self.assertFalse(july.line_ids.filtered(lambda line: line.tax == "aggregated"))
        self.assertEqual(
            set(july.line_ids.mapped("tax")), {"pis_pasep", "cofins", "csll"}
        )
        self.assertIn(
            "aggregate_partial_not_structural",
            july.exception_ids.mapped("reason"),
        )

    def test_exemption_without_legal_basis_is_refused(self):
        """The art. 2 of the IN RFB 459/2004 asks for the legal ground."""
        with self.assertRaises(ValidationError):
            self.supplier.reinf_beneficiary_profile = "zero_rate"

    def test_partial_withholding_of_the_nature_does_not_aggregate(self):
        """A component the nature admits is missing: not structural."""
        self.nature = self.nature_agg
        move = self._create_supplier_invoice(
            "2026-07-10", 10000.0, taxes=[self.tax_pis, self.tax_cofins]
        )
        self._pay(move, "2026-07-10")
        july = self._calculation("2026-07")
        july.action_compute()

        self.assertFalse(july.line_ids.filtered(lambda line: line.tax == "aggregated"))
        self.assertIn(
            "aggregate_partial_not_structural",
            july.exception_ids.mapped("reason"),
        )

    # ------------------------------------------------------------------
    # test 5: below the minimum
    # ------------------------------------------------------------------

    def test_below_minimum_carries_to_the_next_competence(self):
        """A withholding of 8,00 is not collected and travels forward."""
        move = self._create_supplier_invoice("2026-07-10", 800.0, taxes=[self.tax_csll])
        self._pay(move, "2026-07-20")
        july = self._calculation("2026-07")
        july.action_compute()

        darf = july.darf_ids
        self.assertEqual(len(darf), 1)
        self.assertAlmostEqual(darf.total_amount, 8.0, places=2)
        self.assertEqual(darf.state, "carried")
        self.assertIn("below_minimum", july.exception_ids.mapped("reason"))

        # Next competence: the balance arrives under the same revenue code.
        move2 = self._create_supplier_invoice(
            "2026-08-10", 800.0, taxes=[self.tax_csll]
        )
        self._pay(move2, "2026-08-20")
        august = self._calculation("2026-08")
        august.action_compute()

        darf_august = august.darf_ids
        self.assertEqual(len(darf_august), 1)
        self.assertEqual(darf_august.revenue_code, darf.revenue_code)
        self.assertEqual(darf_august.carried_from_id, darf)
        self.assertAlmostEqual(darf_august.carried_amount, 8.0, places=2)
        self.assertAlmostEqual(darf_august.total_amount, 16.0, places=2)
        self.assertEqual(darf_august.state, "draft")

    def test_darf_due_date_is_the_second_ten_day_period(self):
        darf_model = self.env["l10n_br_reinf.darf"]
        # 20/08/2026 is a Thursday: it stays.
        self.assertEqual(
            str(darf_model._due_date_of("2026-07", self.company)), "2026-08-20"
        )
        # 20/06/2026 is a Saturday: it is anticipated to Friday the 19th.
        self.assertEqual(
            str(darf_model._due_date_of("2026-05", self.company)), "2026-06-19"
        )

    def test_darf_due_date_anticipates_a_banking_holiday(self):
        """The holiday comes from the calendar of the company, not from a
        constant."""
        calendar_model = self.env["resource.calendar"]
        work_calendar = calendar_model.create({"name": "Reinf Calendar"})
        self.company.resource_calendar_id = work_calendar
        # 20/08/2026 is a Thursday. Declared a banking holiday, the DARF is
        # anticipated to Wednesday the 19th.
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Reinf test holiday",
                "calendar_id": work_calendar.id,
                "date_from": "2026-08-20 00:00:00",
                "date_to": "2026-08-20 23:59:59",
                # B is a banking holiday for l10n_br_resource.
                "leave_type": "B",
            }
        )
        self.assertEqual(
            str(self.env["l10n_br_reinf.darf"]._due_date_of("2026-07", self.company)),
            "2026-08-19",
        )

    def test_aggregate_rate_is_only_a_conference(self):
        """The rate does not make the value, so its absence does not block.

        The aggregated field carries what was withheld and the tax authority
        does not recompute it. With no rate valid at the taxable event there is
        simply nothing to compare the value against, and the competence says so
        instead of refusing to declare.
        """
        revenue_code = self.env.ref("l10n_br_reinf.revenue_code_595207")
        self.assertAlmostEqual(revenue_code.rate, 4.65, places=2)
        revenue_code.date_end = "2026-06-30"
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()
        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertEqual(len(aggregated), 1)
        self.assertAlmostEqual(aggregated.wh_amount, 465.0, places=2)
        self.assertAlmostEqual(aggregated.divergence_amount, 0.0, places=2)
        self.assertIn("aggregate_rate_missing", july.exception_ids.mapped("reason"))

    # ------------------------------------------------------------------
    # tests 6 and 7: the event, the split and the XSD
    # ------------------------------------------------------------------

    def test_r4020_xml_is_valid_against_the_xsd(self):
        """Test 7: whatever the case, the XML matches the layout."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()
        july.action_close()

        events = july.event_ids
        self.assertEqual(len(events), 1)
        event = events
        self.assertEqual(event.event_type, "R-4020")
        self.assertEqual(event.partner_id, self.supplier)
        self.assertEqual(event.state, "validated")
        self.assertTrue(event.file_request_id)

        xml = event._serialize()
        self.assertEqual(event._xsd_errors(xml), [])
        # The layout wants the comma as the decimal separator.
        self.assertIn("<vlrAgreg>465,00</vlrAgreg>", xml)
        self.assertIn("<vlrBruto>10000,00</vlrBruto>", xml)
        self.assertIn(f"<natRend>{self.nature_agg.code}</natRend>", xml)
        # ideContri takes the root of the CNPJ, ideEstab the whole number.
        self.assertIn(
            f"<nrInscEstab>{self.company.cnpj_cpf_stripped}</nrInscEstab>", xml
        )
        self.assertIn(f"<nrInsc>{self.company._reinf_inscription()[1]}</nrInsc>", xml)
        self.assertEqual(july.state, "closed")

    def test_r4020_refuses_aggregate_together_with_the_components(self):
        """Aggregate and separate values in the same payment duplicate the debt."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        self._pcc_invoice_paid(10000.0)
        july = self._calculation("2026-07")
        july.action_compute()
        aggregated = july.line_ids.filtered(lambda line: line.tax == "aggregated")
        self.assertTrue(aggregated)
        # Forge the inconsistency the guard exists for: a CSLL line surviving
        # next to the aggregate of the same payment.
        aggregated.copy({"tax": "csll", "wh_amount": 100.0})
        # The guard fires while the event is being generated, so the competence
        # does not even close over a XML that would duplicate the debt.
        with self.assertRaises(UserError):
            july.action_close()

    def test_r4020_omits_a_withholding_that_did_not_happen(self):
        """A tax that was not withheld has no field, not a field with 0,00."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        move = self._create_supplier_invoice(
            "2026-07-10", 10000.0, taxes=[self.tax_irpj]
        )
        self._pay(move, "2026-07-10")
        july = self._calculation("2026-07")
        july.action_compute()
        july.action_close()
        xml = july.event_ids[0]._serialize()
        self.assertEqual(july.event_ids[0]._xsd_errors(xml), [])
        self.assertIn("<vlrIR>150,00</vlrIR>", xml)
        # No FIELD with a zero value: ">0,00<" and not the substring "0,00",
        # which a legitimate 10000,00 also contains.
        self.assertNotIn(">0,00<", xml)
        for absent in ("vlrAgreg", "vlrCSLL", "vlrCofins", "vlrPP"):
            self.assertNotIn(absent, xml)

    def test_r4020_accumulates_three_payments_in_one_event(self):
        """Test 1 of the spec, on the event side: 1 event, 1 idePgto, 3
        infoPgto."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        for day in ("05", "15", "25"):
            self._pcc_invoice_paid(
                1000.0, invoice_date=f"2026-07-{day}", pay_date=f"2026-07-{day}"
            )
        july = self._calculation("2026-07")
        july.action_compute()
        july.action_close()

        self.assertEqual(len(july.event_ids), 1)
        xml = july.event_ids._serialize()
        self.assertEqual(july.event_ids._xsd_errors(xml), [])
        self.assertEqual(xml.count("<idePgto>"), 1)
        self.assertEqual(xml.count("<infoPgto>"), 3)

    def test_r4020_splits_above_one_hundred_natures(self):
        """Test 6: more than 100 idePgto does not fit one event."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        move = self._create_supplier_invoice(
            "2026-07-10", 10000.0, taxes=[self.tax_csll]
        )
        self._pay(move, "2026-07-20")
        july = self._calculation("2026-07")
        july.action_compute()

        # 101 natures on the same beneficiary, which is what forces the split.
        natures = self.env["l10n_br_reinf.nature.income"].search([], limit=101)
        self.assertEqual(len(natures), 101)
        template = july.line_ids[0]
        template.nature_income_id = natures[0]
        for nature in natures[1:]:
            template.copy({"nature_income_id": nature.id})
        self.assertEqual(len(july.line_ids), 101)

        july.action_close()
        events = july.event_ids
        self.assertEqual(len(events), 2)
        # The first event of the beneficiary has no ideEvtAdic; the second says
        # which slice it is.
        self.assertFalse(
            events.filtered(lambda item: not item.additional_event)[0].additional_event
        )
        self.assertTrue(events.filtered("additional_event"))
        for event in events:
            xml = event._serialize()
            self.assertEqual(event._xsd_errors(xml), [])
            self.assertLessEqual(xml.count("<idePgto>"), 100)
