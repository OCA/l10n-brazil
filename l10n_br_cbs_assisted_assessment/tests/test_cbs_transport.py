# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import CLIENT_CLASS, CREDITS_FILE, DEBITS_FILE

CBS_REQUEST_LOG = (
    "odoo.addons.l10n_br_cbs_assisted_assessment.models.assisted_assessment_request"
)


class TestCbsTransport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The gateway requires HTTPS; tests run on http://localhost and also
        # exercise refusals, invalid periods and a failed poll. Mute the
        # transport logger so checklog-odoo does not treat those as failures.
        mute = mute_logger(CBS_REQUEST_LOG)
        mute.__enter__()
        cls.addClassCleanup(lambda: mute.__exit__(None, None, None))
        cls.company = cls.env.company
        cls.company.write(
            {
                "cbs_assessment_client_id": "client-id",
                "cbs_assessment_client_secret": "client-secret",
            }
        )
        cls.company.partner_id.vat = "11.222.333/0001-81"
        cls.request_model = cls.env["l10n_br_assessment.request"]
        cls.period_model = cls.env["l10n_br_assessment.period"]

    def _new_request(self, service="debits", **vals):
        return self.request_model.create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "service": service,
                **vals,
            }
        )

    def test_cnpj_root_uses_the_first_eight_digits(self):
        self.assertEqual(self.company._assessment_cnpj_root(), "11222333")

    def test_period_conversion(self):
        self.assertEqual(self.request_model._per_apur_from_pa("06/2026"), "2026-06")
        self.assertEqual(self.request_model._per_apur_from_pa("6/2026"), "2026-06")
        self.assertFalse(self.request_model._per_apur_from_pa("2026-06"))
        self.assertFalse(self.request_model._per_apur_from_pa(""))

    def test_parse_debits_groups_by_period(self):
        request = self._new_request(payload=json.dumps(DEBITS_FILE))
        parsed = request._parse_payload()
        self.assertEqual(sorted(parsed), ["2026-06", "2026-08"])
        line = parsed["2026-06"][0]
        self.assertEqual(line["value"], 80)
        self.assertEqual(line["value_balance"], 80)
        self.assertEqual(line["document_model"], 55)
        self.assertEqual(line["origin"], 0)
        self.assertEqual(
            fields.Datetime.to_string(line["date_emission"]), "2026-06-03 04:53:58"
        )
        self.assertEqual(line["value_detail"]["saldoDevedor"], 80)

    def test_parse_credits_flattens_the_appropriation_group(self):
        request = self._new_request(service="credits", payload=json.dumps(CREDITS_FILE))
        line = request._parse_payload()["2026-08"][0]
        self.assertEqual(line["value"], 15)
        self.assertEqual(line["value_suspended"], 3)
        self.assertEqual(line["value_balance"], 7)

    def test_parse_skips_unexpected_periods(self):
        payload = {"apuracao": [{"pa": "invalid", "debitos": [{"chave": "x"}]}]}
        request = self._new_request(payload=json.dumps(payload))
        self.assertEqual(request._parse_payload(), {})

    def test_parse_rejects_invalid_json(self):
        request = self._new_request(payload="not json")
        with self.assertRaises(UserError):
            request._parse_payload()

    def test_parse_rejects_a_service_without_lines(self):
        request = self._new_request(service="payments", payload="{}")
        with self.assertRaises(UserError):
            request._parse_payload()

    def test_transmit_stores_the_ticket(self):
        request = self._new_request()
        answer = {"tiqueteSolicitacao": "692b7b25.B5E08D55", "tEASegundos": "120"}
        with patch(f"{CLIENT_CLASS}._open_request", return_value=answer) as opened:
            request.action_transmit()
        self.assertEqual(request.state, "requested")
        self.assertEqual(request.ticket, "692b7b25.B5E08D55")
        self.assertEqual(request.estimated_seconds, 120)
        self.assertTrue(request.request_date)
        self.assertTrue(request.return_url)
        self.assertEqual(opened.call_args.args[1], "debits")

    def test_transmit_generates_the_callback_token_once(self):
        answer = {"tiqueteSolicitacao": "a", "tEASegundos": "1"}
        with patch(f"{CLIENT_CLASS}._open_request", return_value=answer):
            self._new_request().action_transmit()
            token = self.company.cbs_assessment_webhook_token
            self._new_request(service="credits").action_transmit()
        self.assertTrue(token)
        self.assertEqual(self.company.cbs_assessment_webhook_token, token)

    def test_transmit_reports_a_refusal(self):
        request = self._new_request()
        answer = {"codigoErro": "APURACAO-001", "mensagemErro": "Invalid parameters"}
        with patch(f"{CLIENT_CLASS}._open_request", return_value=answer):
            request.action_transmit()
        self.assertEqual(request.state, "error")
        self.assertEqual(request.error_code, "APURACAO-001")
        self.assertEqual(request.error_message, "Invalid parameters")
        # The call was charged by the gateway, so it has to count for the quota.
        self.assertTrue(request.request_date)

    def test_status_poll_marks_the_request_ready(self):
        request = self._new_request(state="requested", ticket="692b7b25.B5E08D55")
        answer = {
            "estado": "CONCLUIDA",
            "urlAssinada": "https://storage.example.com/file.json?X-Amz-Signature=x",
            "urlAssinadaExpiraEm": "2026-08-26T14:30:00Z",
        }
        with patch(f"{CLIENT_CLASS}._get_status", return_value=answer):
            request.action_check_status()
        self.assertEqual(request.state, "notified")
        self.assertTrue(request.signed_url)

    def test_status_poll_keeps_waiting_while_processing(self):
        request = self._new_request(state="requested", ticket="t")
        with patch(
            f"{CLIENT_CLASS}._get_status", return_value={"estado": "EM_PROCESSAMENTO"}
        ):
            request.action_check_status()
        self.assertEqual(request.state, "requested")

    def test_status_poll_reports_the_error(self):
        request = self._new_request(state="requested", ticket="t")
        answer = {
            "estado": "ERRO",
            "codigoErro": "APURACAO-408",
            "mensagemErro": "Timeout",
        }
        with patch(f"{CLIENT_CLASS}._get_status", return_value=answer):
            request.action_check_status()
        self.assertEqual(request.state, "error")
        self.assertEqual(request.error_code, "APURACAO-408")

    def test_status_poll_requires_a_ticket(self):
        with self.assertRaises(UserError):
            self._new_request(state="requested").action_check_status()

    def test_full_cycle_feeds_the_periods(self):
        request = self._new_request()
        opened = {"tiqueteSolicitacao": "692b7b25.B5E08D55", "tEASegundos": "120"}
        status = {
            "estado": "CONCLUIDA",
            "urlAssinada": "https://storage.example.com/file.json",
            "urlAssinadaExpiraEm": "2099-01-01T00:00:00Z",
        }
        with (
            patch(f"{CLIENT_CLASS}._open_request", return_value=opened),
            patch(f"{CLIENT_CLASS}._get_status", return_value=status),
            patch(f"{CLIENT_CLASS}._download", return_value=json.dumps(DEBITS_FILE)),
        ):
            request.action_transmit()
            request.action_check_status()
            request.action_download()
            request.action_apply()
        self.assertEqual(request.state, "done")
        self.assertEqual(len(request.period_ids), 2)
        june = self.period_model._get_or_create(self.company, "cbs", "2026-06")
        self.assertEqual(june.fisco_debit, 80)
        self.assertEqual(june.state, "received")

    def test_poll_cron_advances_pending_requests(self):
        request = self._new_request(state="requested", ticket="692b7b25.B5E08D55")
        status = {
            "estado": "CONCLUIDA",
            "urlAssinada": "https://storage.example.com/file.json",
            "urlAssinadaExpiraEm": "2099-01-01T00:00:00Z",
        }
        with (
            patch(f"{CLIENT_CLASS}._get_status", return_value=status),
            patch(f"{CLIENT_CLASS}._download", return_value=json.dumps(DEBITS_FILE)),
        ):
            self.request_model._cron_poll_requests()
            self.request_model._cron_poll_requests()
        self.assertEqual(request.state, "done")

    def test_poll_cron_survives_a_transport_failure(self):
        request = self._new_request(state="requested", ticket="t")
        with patch(f"{CLIENT_CLASS}._get_status", side_effect=UserError("boom")):
            self.request_model._cron_poll_requests()
        self.assertEqual(request.state, "requested")

    def test_client_requires_credentials(self):
        self.company.cbs_assessment_client_id = False
        with self.assertRaises(UserError):
            self.env["l10n_br_cbs_assessment.client"]._get_token(self.company)

    def test_client_requires_the_cnpj_root(self):
        self.company.partner_id.vat = False
        self.company.vat = False
        with patch(f"{CLIENT_CLASS}._get_token", return_value="token"):
            with self.assertRaises(UserError):
                self.env["l10n_br_cbs_assessment.client"]._open_request(
                    self.company, "debits", "https://example.com/hook"
                )

    def test_client_rejects_an_unsupported_service(self):
        with self.assertRaises(UserError):
            self.env["l10n_br_cbs_assessment.client"]._open_request(
                self.company, "payments", "https://example.com/hook"
            )

    def test_base_url_follows_the_environment(self):
        client = self.env["l10n_br_cbs_assessment.client"]
        self.assertTrue(client._base_url(self.company).endswith("/apuracao-cbs-prr/v2"))
        self.company.cbs_assessment_environment = "production"
        self.assertTrue(client._base_url(self.company).endswith("/apuracao-cbs/v2"))
