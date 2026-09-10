# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import json

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDctfwebDemo(TransactionCase):
    """The demo has to show the three shapes the layout takes.

    Demo data fails quietly in Odoo: a warning drops the whole file and the
    install still exits zero. These tests are the guard, so a broken demo is a
    red test and not a database that silently has nothing in it.
    """

    def _demo(self, xmlid):
        record = self.env.ref("l10n_br_dctfweb.%s" % xmlid, raise_if_not_found=False)
        if not record:
            self.skipTest("database without demo data")
        return record.sudo()

    def test_the_demo_tax_groups_carry_their_revenue_code(self):
        """Without the mapping the assessment reads nothing at all."""
        pis = self.env.ref("l10n_br_coa.tax_group_pis", raise_if_not_found=False)
        if not pis:
            self.skipTest("database without the Brazilian chart of accounts")
        self.assertEqual(
            pis.sudo().dctfweb_revenue_code_id.mit_code,
            "810902",
            "the cumulative PIS code, the regime the demo assessment uses",
        )
        cofins = self.env.ref("l10n_br_coa.tax_group_cofins").sudo()
        self.assertEqual(cofins.dctfweb_revenue_code_id.mit_code, "217201")

    def test_icms_stays_without_a_code(self):
        """ICMS is not confessed in the MIT: the demo must not map it."""
        icms = self.env.ref("l10n_br_coa.tax_group_icms", raise_if_not_found=False)
        if not icms:
            self.skipTest("database without the Brazilian chart of accounts")
        self.assertFalse(icms.sudo().dctfweb_revenue_code_id)

    def test_the_demo_company_has_its_initial_data(self):
        company = self.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        if not company:
            self.skipTest("database without demo data")
        company = company.sudo()
        self.assertEqual(company.dctfweb_pj_qualification, "1")
        self.assertEqual(company.dctfweb_profit_taxation, "3")
        self.assertTrue(company.dctfweb_responsible_cpf)

    def test_the_current_assessment_is_assessed_for_the_current_month(self):
        mit = self._demo("demo_mit_current")
        today = self.env.cr.now().date() if hasattr(self.env.cr, "now") else None
        self.assertEqual(mit.state, "assessed")
        if today:
            self.assertEqual(mit.year, today.year)
            self.assertEqual(int(mit.month), today.month)
        self.assertEqual(mit.date_from.day, 1)

    def test_the_current_assessment_read_the_persisted_assessments(self):
        """The point of the demo: the confession comes from the books."""
        mit = self._demo("demo_mit_current")
        assessments = (
            self.env["l10n_br_tax.assessment"]
            .sudo()
            .search(mit._tax_assessment_domain())
        )
        if not assessments:
            self.skipTest("database without tax assessment demo data")
        mapped = assessments.filtered("tax_group_id.dctfweb_revenue_code_id")
        self.assertTrue(
            mapped, "the demo maps PIS, COFINS and IPI to their revenue codes"
        )
        self.assertEqual(mit.tax_assessment_ids, mapped)
        for debit in mit.debit_ids:
            self.assertEqual(debit.source, "computed")
            self.assertTrue(debit.tax_assessment_id)

    def test_the_skipped_icms_assessment_is_in_the_chatter(self):
        """Silence about a skipped group would be a trap for the accountant."""
        mit = self._demo("demo_mit_current")
        icms = self.env.ref("l10n_br_coa.tax_group_icms", raise_if_not_found=False)
        if not icms:
            self.skipTest("database without the Brazilian chart of accounts")
        skipped = (
            self.env["l10n_br_tax.assessment"]
            .sudo()
            .search(mit._tax_assessment_domain() + [("tax_group_id", "=", icms.id)])
        )
        if not skipped:
            self.skipTest("database without an ICMS assessment in the period")
        self.assertTrue(
            any(skipped.name in str(message.body) for message in mit.message_ids),
            "the assessment posts which groups it skipped",
        )

    def test_the_assessment_without_movement_is_closed_and_has_a_file(self):
        mit = self._demo("demo_mit_no_movement")
        self.assertEqual(mit.state, "closed")
        self.assertTrue(mit.no_movement)
        self.assertFalse(mit.debit_ids)
        self.assertTrue(mit.mit_file, "closing has to build the file")
        payload = json.loads(base64.b64decode(mit.mit_file).decode())
        self.assertIs(payload["DadosIniciais"]["SemMovimento"], True)
        self.assertNotIn("Debitos", payload)
        self.assertTrue(mit.mit_filename.endswith(".json"))
        self.assertIn("-MIT-", mit.mit_filename)

    def test_the_suspension_demo_confesses_the_whole_debit(self):
        """A suspended debit is not a smaller debit."""
        mit = self._demo("demo_mit_suspension")
        debit = self._demo("demo_debit_cofins")
        self.assertEqual(debit.amount, 3200.0)
        self.assertEqual(mit.debit_total, 3200.0)
        self.assertEqual(mit.suspended_total, 1200.0)

    def test_the_suspension_demo_is_a_lawsuit_with_its_court(self):
        suspension = self._demo("demo_suspension_cofins")
        self.assertEqual(suspension.suspension_type, "2")
        self.assertEqual(suspension.reason, "1")
        self.assertTrue(suspension.decision_date)
        self.assertTrue(suspension.court_city_id.ibge_code)
        payload = suspension._build_payload()
        self.assertEqual(payload["TipoSuspensao"], 2)
        self.assertEqual(payload["MotivoSuspensao"], 1)
        self.assertEqual(len(payload["ListaDebitosSuspensos"]), 1)

    def test_the_suspension_demo_has_no_pendency(self):
        """The demo has to be closeable: a demo that cannot close teaches
        nothing."""
        mit = self._demo("demo_mit_suspension")
        self.assertEqual(mit._check_pendencies(), [])

    def test_the_suspension_demo_payload_is_complete(self):
        mit = self._demo("demo_mit_suspension")
        payload = mit._build_mit_payload()
        self.assertIn("PeriodoApuracao", payload)
        self.assertIn("DadosIniciais", payload)
        self.assertEqual(
            payload["Debitos"]["Cofins"]["ListaDebitos"][0]["ValorDebito"], 3200.0
        )
        self.assertEqual(
            payload["ListaSuspensoes"][0]["ListaDebitosSuspensos"][0]["ValorSuspenso"],
            1200.0,
        )
