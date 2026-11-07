# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import json

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMitPayload(AccountTestInvoicingCommon):
    """The payload has to be what the layout says, field by field.

    Reference: MIT JSON import layout 1.0, rectified on 2025-02-20, and the
    schema 1.0 published with it (ADE CORAT 19/2024).
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.company.write({"cnpj_cpf": "12.345.678/0001-95"})
        cls.code_pis = cls.env.ref("l10n_br_dctfweb.revenue_code_810902")
        cls.code_cofins = cls.env.ref("l10n_br_dctfweb.revenue_code_217201")
        cls.code_ipi = cls.env.ref("l10n_br_dctfweb.revenue_code_066803")
        cls.code_irpj = cls.env.ref("l10n_br_dctfweb.revenue_code_022001")
        cls.code_irpj_postponed = cls.env.ref("l10n_br_dctfweb.revenue_code_022010")
        cls.code_irpj_annual = cls.env.ref("l10n_br_dctfweb.revenue_code_243001")
        cls.code_irpj_scp = cls.env.ref("l10n_br_dctfweb.revenue_code_022008")
        cls.city = cls.env["res.city"].search([("country_id.code", "=", "BR")], limit=1)

    def _mit(self, **values):
        base = {
            "company_id": self.company.id,
            "year": 2026,
            "month": "4",
            "pj_qualification": "1",
            "profit_taxation": "3",
            "monetary_variation": "2",
            "pis_cofins_regime": "2",
            "responsible_cpf": "07206845000",
        }
        base.update(values)
        return self.env["l10n_br_dctfweb.assessment"].create(base)

    def _debit(self, mit, code, amount=100.0, **values):
        base = {
            "assessment_id": mit.id,
            "revenue_code_id": code.id,
            "amount": amount,
        }
        base.update(values)
        return self.env["l10n_br_dctfweb.debit"].create(base)

    # ------------------------------------------------------------------

    def test_the_period_is_written_as_numbers(self):
        payload = self._mit()._build_mit_payload()
        self.assertEqual(
            payload["PeriodoApuracao"], {"MesApuracao": 4, "AnoApuracao": 2026}
        )

    def test_the_two_required_objects_are_always_there(self):
        """Schema: required ["PeriodoApuracao", "DadosIniciais"]."""
        payload = self._mit(no_movement=True)._build_mit_payload()
        self.assertIn("PeriodoApuracao", payload)
        self.assertIn("DadosIniciais", payload)

    def test_the_initial_data_carries_what_the_schema_requires(self):
        """Schema: required ["SemMovimento", "QualificacaoPj",
        "ResponsavelApuracao"]."""
        data = self._mit()._build_mit_payload()["DadosIniciais"]
        self.assertIs(data["SemMovimento"], False)
        self.assertEqual(data["QualificacaoPj"], 1)
        self.assertEqual(data["ResponsavelApuracao"]["CpfResponsavel"], "07206845000")
        self.assertEqual(data["TributacaoLucro"], 3)
        self.assertEqual(data["VariacoesMonetarias"], 2)
        self.assertEqual(data["RegimePisCofins"], 2)

    def test_without_movement_the_initial_data_stops_at_the_qualification(self):
        """Layout: TributacaoLucro and the others only when SemMovimento is
        false."""
        data = self._mit(no_movement=True)._build_mit_payload()["DadosIniciais"]
        self.assertIs(data["SemMovimento"], True)
        self.assertNotIn("TributacaoLucro", data)
        self.assertNotIn("VariacoesMonetarias", data)
        self.assertNotIn("RegimePisCofins", data)

    def test_without_movement_there_are_no_debits(self):
        mit = self._mit(no_movement=True)
        payload = mit._build_mit_payload()
        self.assertNotIn("Debitos", payload)
        self.assertNotIn("ListaSuspensoes", payload)

    def test_the_phone_and_the_crc_are_optional_objects(self):
        mit = self._mit()
        data = mit._build_mit_payload()["DadosIniciais"]["ResponsavelApuracao"]
        self.assertNotIn("TelResponsavel", data)
        self.assertNotIn("RegistroCrc", data)
        state = self.env["res.country.state"].search(
            [("country_id.code", "=", "BR")], limit=1
        )
        mit.write(
            {
                "responsible_phone_area": "35",
                "responsible_phone": "999991111",
                "responsible_email": "responsavel@example.com",
                "crc_state_id": state.id,
                "crc_number": "123456",
            }
        )
        data = mit._build_mit_payload()["DadosIniciais"]["ResponsavelApuracao"]
        self.assertEqual(
            data["TelResponsavel"], {"Ddd": "35", "NumTelefone": "999991111"}
        )
        self.assertEqual(data["EmailResponsavel"], "responsavel@example.com")
        self.assertEqual(data["RegistroCrc"]["UfRegistro"], state.code)
        self.assertEqual(data["RegistroCrc"]["NumRegistro"], "123456")

    # ------------------------------------------------------------------
    # Debits
    # ------------------------------------------------------------------

    def test_a_debit_carries_the_three_required_fields(self):
        """Schema: required ["IdDebito", "CodigoDebito", "ValorDebito"]."""
        mit = self._mit()
        self._debit(mit, self.code_pis, 1234.56)
        debit = mit._build_mit_payload()["Debitos"]["PisPasep"]["ListaDebitos"][0]
        self.assertEqual(debit["IdDebito"], 1)
        self.assertEqual(debit["CodigoDebito"], "810902")
        self.assertEqual(debit["ValorDebito"], 1234.56)

    def test_the_debit_code_is_six_digits_as_a_string(self):
        mit = self._mit()
        self._debit(mit, self.code_irpj)
        debit = mit._build_mit_payload()["Debitos"]["Irpj"]["ListaDebitos"][0]
        self.assertIsInstance(debit["CodigoDebito"], str)
        self.assertEqual(len(debit["CodigoDebito"]), 6)

    def test_the_groups_are_written_in_the_order_the_layout_requires(self):
        """Layout: the debits must be informed in the order of the table."""
        mit = self._mit()
        self._debit(mit, self.code_cofins)
        self._debit(mit, self.code_pis)
        self._debit(mit, self.code_irpj)
        self._debit(mit, self.code_ipi, establishment_cnpj="000198")
        keys = [
            key
            for key in mit._build_mit_payload()["Debitos"]
            if key != "BalancoLucroReal"
        ]
        self.assertEqual(keys, ["Irpj", "Ipi", "PisPasep", "Cofins"])

    def test_an_empty_group_is_not_written(self):
        mit = self._mit()
        self._debit(mit, self.code_pis)
        self.assertEqual(list(mit._build_mit_payload()["Debitos"]), ["PisPasep"])

    def test_the_ipi_debit_writes_the_establishment(self):
        """Schema: CnpjEstabelecimento is required for Ipi."""
        mit = self._mit()
        self._debit(mit, self.code_ipi, establishment_cnpj="000198")
        debit = mit._build_mit_payload()["Debitos"]["Ipi"]["ListaDebitos"][0]
        self.assertEqual(debit["CnpjEstabelecimento"], "000198")

    def test_a_postponed_debit_writes_the_year_and_the_quarter(self):
        mit = self._mit()
        self._debit(
            mit,
            self.code_irpj_postponed,
            postponed_year=2024,
            postponed_quarter="2",
        )
        debit = mit._build_mit_payload()["Debitos"]["Irpj"]["ListaDebitos"][0]
        self.assertEqual(debit["AnoPostergado"], 2024)
        self.assertEqual(debit["TrimPostergado"], 2)
        self.assertNotIn("AnoDebito", debit)

    def test_an_annual_debit_writes_the_debit_year(self):
        mit = self._mit()
        self._debit(mit, self.code_irpj_annual, debit_year=2025)
        debit = mit._build_mit_payload()["Debitos"]["Irpj"]["ListaDebitos"][0]
        self.assertEqual(debit["AnoDebito"], 2025)
        self.assertNotIn("AnoPostergado", debit)

    def test_a_joint_venture_debit_writes_the_scp_cnpj(self):
        mit = self._mit()
        self._debit(mit, self.code_irpj_scp, scp_cnpj="12345678000195")
        debit = mit._build_mit_payload()["Debitos"]["Irpj"]["ListaDebitos"][0]
        self.assertEqual(debit["CnpjScp"], "12345678000195")

    def test_a_code_that_does_not_accept_an_attribute_never_writes_it(self):
        """A stale attribute would be refused by the authority."""
        mit = self._mit()
        self._debit(mit, self.code_pis, scp_cnpj="12345678000195", period=5)
        debit = mit._build_mit_payload()["Debitos"]["PisPasep"]["ListaDebitos"][0]
        self.assertNotIn("CnpjScp", debit)
        self.assertNotIn("PaDebito", debit)

    def test_the_gold_debit_writes_the_city_code(self):
        mit = self._mit()
        self._debit(
            mit,
            self.env.ref("l10n_br_dctfweb.revenue_code_402802"),
            period=2,
            gold_city_id=self.city.id,
        )
        debit = mit._build_mit_payload()["Debitos"]["Iof"]["ListaDebitos"][0]
        self.assertEqual(debit["PaDebito"], 2)
        self.assertEqual(debit["CodigoMunicipioOuro"], self.city.ibge_code)

    def test_the_real_profit_balance_only_exists_for_annual_actual_profit(self):
        mit = self._mit(profit_taxation="3")
        self._debit(mit, self.code_pis)
        self.assertNotIn("BalancoLucroReal", mit._build_mit_payload()["Debitos"])
        mit.write({"profit_taxation": "1", "real_profit_balance": True})
        self.assertIs(mit._build_mit_payload()["Debitos"]["BalancoLucroReal"], True)

    def test_a_negative_debit_is_refused(self):
        mit = self._mit()
        with self.assertRaises(ValidationError):
            self._debit(mit, self.code_pis, -10.0)

    # ------------------------------------------------------------------
    # Special events
    # ------------------------------------------------------------------

    def test_the_special_events_are_numbered_in_chronological_order(self):
        mit = self._mit()
        second = self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 20, "event_type": "4"}
        )
        first = self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 5, "event_type": "4"}
        )
        self.assertEqual(first.event_number, 1)
        self.assertEqual(second.event_number, 2)
        events = mit._build_mit_payload()["ListaEventosEspeciais"]
        self.assertEqual([event["DiaEvento"] for event in events], [5, 20])
        self.assertEqual([event["IdEvento"] for event in events], [1, 2])

    def test_two_events_on_the_same_day_are_refused(self):
        mit = self._mit()
        self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 5, "event_type": "4"}
        )
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dctfweb.special.event"].create(
                {"assessment_id": mit.id, "day": 5, "event_type": "6"}
            )

    def test_a_day_outside_the_month_is_refused(self):
        mit = self._mit(month="4")
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dctfweb.special.event"].create(
                {"assessment_id": mit.id, "day": 31, "event_type": "4"}
            )

    def test_a_debit_after_the_last_event_goes_to_its_own_list(self):
        mit = self._mit()
        event = self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 10, "event_type": "4"}
        )
        self._debit(mit, self.code_pis, 100.0, special_event_id=event.id)
        self._debit(mit, self.code_pis, 50.0, after_special_event=True)
        group = mit._build_mit_payload()["Debitos"]["PisPasep"]
        self.assertEqual(len(group["ListaDebitos"]), 1)
        self.assertEqual(group["ListaDebitos"][0]["IdEventoDebito"], event.event_number)
        self.assertEqual(len(group["ListaDebitosAposEvento"]), 1)
        self.assertNotIn("IdEventoDebito", group["ListaDebitosAposEvento"][0])

    def test_with_events_the_debit_needs_to_say_which_one(self):
        mit = self._mit()
        self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 10, "event_type": "4"}
        )
        self._debit(mit, self.code_pis)
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("event its taxable facts" in pendency for pendency in pendencies),
            pendencies,
        )

    def test_with_events_the_real_profit_balance_is_not_written(self):
        """Layout: BalancoLucroReal is refused when there are special events."""
        mit = self._mit(profit_taxation="1", real_profit_balance=True)
        event = self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 10, "event_type": "4"}
        )
        self._debit(mit, self.code_pis, special_event_id=event.id)
        self.assertNotIn("BalancoLucroReal", mit._build_mit_payload()["Debitos"])

    # ------------------------------------------------------------------
    # Suspensions
    # ------------------------------------------------------------------

    def _suspension(self, mit, debit, **values):
        amount = values.pop("amount", 40.0)
        base = {
            "assessment_id": mit.id,
            "suspension_type": "1",
            "process_number": "12345987654202450",
        }
        base.update(values)
        suspension = self.env["l10n_br_dctfweb.suspension"].create(base)
        self.env["l10n_br_dctfweb.suspension.line"].create(
            {
                "suspension_id": suspension.id,
                "debit_id": debit.id,
                "amount": amount,
            }
        )
        return suspension

    def test_an_administrative_suspension_writes_only_its_own_fields(self):
        mit = self._mit()
        debit = self._debit(mit, self.code_pis)
        self._suspension(mit, debit)
        suspension = mit._build_mit_payload()["ListaSuspensoes"][0]
        self.assertEqual(suspension["TipoSuspensao"], 1)
        self.assertEqual(suspension["NumeroProcesso"], "12345987654202450")
        self.assertNotIn("MotivoSuspensao", suspension)
        self.assertNotIn("DataDecisao", suspension)
        self.assertEqual(
            suspension["ListaDebitosSuspensos"],
            [{"IdDebitoSuspenso": debit.debit_number, "ValorSuspenso": 40.0}],
        )

    def test_a_judicial_suspension_writes_the_court_data(self):
        mit = self._mit()
        debit = self._debit(mit, self.code_pis)
        self._suspension(
            mit,
            debit,
            suspension_type="2",
            reason="1",
            with_deposit=True,
            third_party_process=False,
            decision_date="2026-03-09",
            court_number=1,
            court_city_id=self.city.id,
            process_number="98765431220251017777",
        )
        suspension = mit._build_mit_payload()["ListaSuspensoes"][0]
        self.assertEqual(suspension["TipoSuspensao"], 2)
        self.assertEqual(suspension["MotivoSuspensao"], 1)
        self.assertEqual(suspension["DataDecisao"], 20260309)
        self.assertEqual(suspension["VaraJudiciaria"], 1)
        self.assertEqual(suspension["CodigoMunicipioSj"], self.city.ibge_code)
        self.assertIs(suspension["ProcessoTerceiro"], False)
        self.assertIs(suspension["ComDeposito"], True)

    def test_the_full_deposit_reason_does_not_take_the_deposit_flag(self):
        """Layout: ComDeposito only when MotivoSuspensao is not 2."""
        mit = self._mit()
        debit = self._debit(mit, self.code_pis)
        self._suspension(
            mit,
            debit,
            suspension_type="2",
            reason="2",
            decision_date="2026-03-09",
            court_number=1,
            court_city_id=self.city.id,
            process_number="98765431220251017777",
        )
        suspension = mit._build_mit_payload()["ListaSuspensoes"][0]
        self.assertNotIn("ComDeposito", suspension)

    def test_a_suspension_larger_than_the_debit_is_a_pendency(self):
        mit = self._mit()
        debit = self._debit(mit, self.code_pis, 100.0)
        self._suspension(mit, debit, amount=500.0)
        mit.suspension_ids.line_ids.amount = 500.0
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("larger than" in pendency for pendency in pendencies), pendencies
        )

    def test_a_suspension_with_special_events_is_a_pendency(self):
        """Layout: ListaSuspensoes only when there is no ListaEventosEspeciais."""
        mit = self._mit()
        event = self.env["l10n_br_dctfweb.special.event"].create(
            {"assessment_id": mit.id, "day": 10, "event_type": "4"}
        )
        debit = self._debit(mit, self.code_pis, special_event_id=event.id)
        self._suspension(mit, debit)
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("special events" in pendency for pendency in pendencies), pendencies
        )

    def test_a_suspension_cannot_cover_a_debit_of_another_assessment(self):
        mit = self._mit()
        other = self._mit(month="5")
        debit = self._debit(other, self.code_pis)
        suspension = self.env["l10n_br_dctfweb.suspension"].create(
            {
                "assessment_id": mit.id,
                "suspension_type": "1",
                "process_number": "12345987654202450",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dctfweb.suspension.line"].create(
                {
                    "suspension_id": suspension.id,
                    "debit_id": debit.id,
                    "amount": 10.0,
                }
            )

    def test_a_process_number_of_the_wrong_size_is_a_pendency(self):
        mit = self._mit()
        debit = self._debit(mit, self.code_pis)
        self._suspension(mit, debit, process_number="123")
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("20 digits" in pendency for pendency in pendencies), pendencies
        )

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------

    def test_the_file_is_named_after_the_cnpj_root_and_the_period(self):
        """Layout: CNPJ root, "-MIT-", AAAAMM."""
        mit = self._mit()
        self.assertEqual(mit._mit_filename(), "12345678-MIT-202604.json")

    def test_the_exported_file_is_the_payload(self):
        mit = self._mit()
        self._debit(mit, self.code_pis, 10.0)
        mit.state = "assessed"
        mit.action_export_json()
        payload = json.loads(base64.b64decode(mit.mit_file).decode())
        self.assertEqual(payload, mit._build_mit_payload())
        self.assertEqual(payload["PeriodoApuracao"]["MesApuracao"], 4)
