# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

MODELS = "odoo.addons.l10n_br_assisted_assessment.models"
PERIOD_CLASS = f"{MODELS}.assisted_assessment.AssistedAssessment"
REQUEST_CLASS = f"{MODELS}.assisted_assessment_request.AssistedAssessmentRequest"
QUOTA = f"{MODELS}.assisted_assessment_request.DAILY_REQUEST_QUOTA"


class TestAssessmentReconciliation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.period_model = cls.env["l10n_br_assessment.period"]
        cls.request_model = cls.env["l10n_br_assessment.request"]
        cls.period = cls.period_model.create(
            {
                "company_id": cls.company.id,
                "tribute": "cbs",
                "per_apur": "2026-10",
            }
        )

    @staticmethod
    def _key(suffix):
        return f"3526{str(suffix).rjust(40, '0')}"

    def _upsert_debits(self, values, origin=0):
        """Apply a debit increment from ``{access key: assessed value}``."""
        return self.period._upsert_lines(
            [
                {
                    "document_key": key,
                    "origin": origin,
                    "document_model": 55,
                    "value": value,
                    "value_balance": value,
                }
                for key, value in values.items()
            ],
            "debits",
        )

    def _reconcile_against(self, booked):
        with patch(f"{PERIOD_CLASS}._local_values_by_key", return_value=booked):
            self.period._reconcile()
        return self.period.divergence_ids

    def _new_request(self, service="debits", **vals):
        return self.request_model.create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "service": service,
                **vals,
            }
        )

    def test_upsert_sets_totals_and_state(self):
        self._upsert_debits({self._key(1): 100.0, self._key(2): 50.0})
        self.assertEqual(self.period.state, "received")
        self.assertEqual(len(self.period.line_ids), 2)
        self.assertEqual(self.period.fisco_debit, 150.0)
        self.assertEqual(self.period.fisco_credit, 0.0)
        self.assertEqual(self.period.fisco_balance, 150.0)

    def test_increment_updates_without_dropping_previous_lines(self):
        """The endpoints answer with a delta, not with the whole period."""
        self._upsert_debits({self._key(1): 100.0, self._key(2): 50.0})
        self._upsert_debits({self._key(2): 70.0})
        self.assertEqual(len(self.period.line_ids), 2)
        self.assertEqual(self.period.fisco_debit, 170.0)

    def test_same_document_with_two_origins_produces_two_lines(self):
        self._upsert_debits({self._key(1): 100.0})
        self._upsert_debits({self._key(1): 20.0}, origin=55)
        self.assertEqual(len(self.period.line_ids), 2)
        self.assertEqual(self.period.fisco_debit, 120.0)

    def test_origins_are_summed_against_the_booked_document(self):
        self._upsert_debits({self._key(1): 100.0})
        self._upsert_debits({self._key(1): 20.0}, origin=55)
        divergences = self._reconcile_against({"debit": {self._key(1): 120.0}})
        self.assertFalse(divergences)

    def test_previous_balance_reduces_the_assessed_balance(self):
        self._upsert_debits({self._key(1): 100.0})
        self.period.previous_balance = 30.0
        self.assertEqual(self.period.fisco_balance, 70.0)

    def test_reconcile_without_divergence(self):
        self._upsert_debits({self._key(1): 100.0})
        divergences = self._reconcile_against({"debit": {self._key(1): 100.0}})
        self.assertFalse(divergences)
        self.assertEqual(self.period.state, "reconciled")

    def test_tolerance_absorbs_rounding(self):
        self._upsert_debits({self._key(1): 100.0})
        divergences = self._reconcile_against({"debit": {self._key(1): 100.005}})
        self.assertFalse(divergences)

    def test_booked_above_assessed_suggests_a_debit_note(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 130.0}})
        self.assertEqual(divergence.divergence_type, "value")
        self.assertEqual(divergence.suggested_action, "debit_note")
        self.assertEqual(divergence.difference, -30.0)
        self.assertEqual(divergence.line_id, self.period.line_ids)
        self.assertEqual(self.period.state, "diverged")

    def test_assessed_above_booked_suggests_fixing_the_registration(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 80.0}})
        self.assertEqual(divergence.divergence_type, "value")
        self.assertEqual(divergence.suggested_action, "fix_registration")

    def test_document_only_in_the_assessment(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {}})
        self.assertEqual(divergence.divergence_type, "missing_local")
        self.assertEqual(divergence.suggested_action, "register_document")

    def test_document_only_in_the_bookkeeping(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against(
            {"debit": {self._key(1): 100.0, self._key(2): 70.0}}
        )
        self.assertEqual(divergence.divergence_type, "missing_fisco")
        self.assertEqual(divergence.document_key, self._key(2))
        self.assertEqual(divergence.suggested_action, "debit_note")
        self.assertEqual(divergence.local_value, 70.0)
        self.assertFalse(divergence.line_id)

    def test_credit_not_granted(self):
        self.period._upsert_lines(
            [{"document_key": self._key(3), "document_model": 55, "value": 0.0}],
            "credits",
        )
        divergence = self._reconcile_against({"credit": {self._key(3): 90.0}})
        self.assertEqual(divergence.divergence_type, "credit_denied")
        self.assertEqual(divergence.suggested_action, "review_credit")

    def test_directions_not_downloaded_are_not_reported(self):
        """Debits and credits are separate services with separate releases.

        Booked inbound documents must not be reported as missing while the
        credits service has not been downloaded yet.
        """
        self._upsert_debits({self._key(1): 100.0})
        divergences = self._reconcile_against(
            {"debit": {self._key(1): 100.0}, "credit": {self._key(3): 90.0}}
        )
        self.assertFalse(divergences)

    def test_reconcile_requires_downloaded_assessment(self):
        with self.assertRaises(UserError):
            self.period.action_reconcile()

    def test_reconcile_clears_previous_open_divergences(self):
        self._upsert_debits({self._key(1): 100.0})
        self._reconcile_against({"debit": {self._key(1): 130.0}})
        self._reconcile_against({"debit": {self._key(1): 100.0}})
        self.assertFalse(self.period.divergence_ids)
        self.assertEqual(self.period.state, "reconciled")

    def test_confirm_is_blocked_by_open_divergences(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 130.0}})
        with self.assertRaises(UserError):
            self.period.action_confirm()
        divergence.action_mark_handled()
        self.period.action_confirm()
        self.assertEqual(self.period.state, "confirmed")
        self.assertEqual(
            self.period.date_confirmed, fields.Date.context_today(self.period)
        )

    def test_confirm_requires_reconciliation(self):
        self._upsert_debits({self._key(1): 100.0})
        with self.assertRaises(UserError):
            self.period.action_confirm()

    def test_payments_service_produces_no_lines(self):
        with self.assertRaises(UserError):
            self.period._upsert_lines([], "payments")

    def test_get_or_create_reuses_the_existing_period(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-10")
        self.assertEqual(period, self.period)

    def test_get_or_create_creates_a_missing_period(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-07")
        self.assertNotEqual(period, self.period)
        self.assertEqual(period.per_apur, "2026-07")

    def test_created_request_appears_on_the_period_before_apply(self):
        request = self._new_request(period_id=self.period.id, state="requested")
        self.assertIn(request, self.period.all_request_ids)
        self.assertNotIn(request, self.period.request_ids)

    def test_open_request_blocks_another_of_the_same_service(self):
        self._new_request(period_id=self.period.id, state="requested", service="debits")
        with self.assertRaises(UserError):
            self.period.action_request_debits()

    def test_finished_request_does_not_block_a_later_increment(self):
        self._new_request(period_id=self.period.id, state="done", service="debits")
        with patch(f"{REQUEST_CLASS}._transmit", return_value=True):
            request = self.period.action_request_debits()
        self.assertEqual(request.service, "debits")
        self.assertEqual(request.period_id, self.period)

    def test_identical_increment_does_not_post_a_message(self):
        self._upsert_debits({self._key(1): 100.0})
        messages_before = self.period.message_ids
        self._upsert_debits({self._key(1): 100.0})
        self.assertEqual(self.period.message_ids, messages_before)

    def test_line_display_name_uses_type_and_key(self):
        self._upsert_debits({self._key(1): 100.0})
        line = self.period.line_ids
        self.assertIn("Debit", line.display_name)
        self.assertIn(self._key(1), line.display_name)
        self.assertNotIn("l10n_br_assessment.line", line.display_name)

    def test_divergence_display_name_uses_type_and_key(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {}})
        self.assertIn(self._key(1), divergence.display_name)
        self.assertNotIn("l10n_br_assessment.divergence", divergence.display_name)

    def test_period_download_delegates_to_ready_requests(self):
        self._new_request(
            period_id=self.period.id,
            state="notified",
            signed_url="https://storage.example.com/file.json",
        )
        with patch(f"{REQUEST_CLASS}._download", return_value=True) as mocked:
            self.period.action_download_ready_requests()
        mocked.assert_called_once()

    def test_period_apply_delegates_to_downloaded_requests(self):
        self._new_request(period_id=self.period.id, state="downloaded", payload="{}")
        with patch(f"{REQUEST_CLASS}._apply", return_value=True) as mocked:
            self.period.action_apply_downloaded_requests()
        mocked.assert_called_once()

    def test_apply_dispatches_the_answer_across_periods(self):
        """A single answer carries the current period and past adjustments."""
        request = self._new_request(payload="{}")
        parsed = {
            "2026-10": [{"document_key": self._key(1), "value": 100.0}],
            "2026-08": [{"document_key": self._key(2), "value": 40.0}],
        }
        with patch(f"{REQUEST_CLASS}._parse_payload", return_value=parsed):
            request._apply()
        self.assertEqual(request.state, "done")
        self.assertEqual(len(request.period_ids), 2)
        self.assertEqual(self.period.fisco_debit, 100.0)
        adjusted = self.period_model._get_or_create(self.company, "cbs", "2026-08")
        self.assertEqual(adjusted.fisco_debit, 40.0)

    def test_transport_is_required_to_transmit(self):
        with self.assertRaises(UserError):
            self._new_request().action_transmit()

    def test_daily_quota_blocks_the_fifth_call(self):
        for _index in range(4):
            self._new_request(state="requested", request_date=fields.Datetime.now())
        with patch(QUOTA, 4), self.assertRaises(UserError):
            self._new_request()._check_quota()

    def test_refused_requests_consume_the_quota(self):
        """A refusal is charged by the gateway, so it counts."""
        for _index in range(4):
            self._new_request(state="error", request_date=fields.Datetime.now())
        with patch(QUOTA, 4), self.assertRaises(UserError):
            self._new_request()._check_quota()

    def test_untransmitted_requests_do_not_consume_the_quota(self):
        for _index in range(4):
            self._new_request(state="error")
        with patch(QUOTA, 4):
            self.assertTrue(self._new_request()._check_quota())

    def test_quota_is_per_service(self):
        for _index in range(4):
            self._new_request(state="requested", request_date=fields.Datetime.now())
        with patch(QUOTA, 4):
            self.assertTrue(self._new_request(service="credits")._check_quota())

    def test_callback_stores_the_signed_url(self):
        request = self._new_request(state="requested")
        request.register_callback(
            {
                "tiqueteSolicitacao": "692b7b25.B5E08D55",
                "urlAssinada": "https://storage.example.com/file.json?X-Amz-Signature=x",
                "urlAssinadaExpiraEm": "2026-08-26T14:30:00Z",
            }
        )
        self.assertEqual(request.state, "notified")
        self.assertTrue(request.signed_url)
        self.assertEqual(
            fields.Datetime.to_string(request.signed_url_expires_at),
            "2026-08-26 14:30:00",
        )

    def test_callback_reports_the_error(self):
        request = self._new_request(state="requested")
        request.register_callback(
            {"codigoErro": "APURACAO-408", "mensagemErro": "Timeout"}
        )
        self.assertEqual(request.state, "error")
        self.assertEqual(request.error_code, "APURACAO-408")

    def test_unparseable_expiry_is_ignored(self):
        request = self._new_request(state="requested")
        with mute_logger(
            "odoo.addons.l10n_br_assisted_assessment.models.assisted_assessment_request"
        ):
            request.register_callback(
                {"urlAssinada": "https://x", "urlAssinadaExpiraEm": "?"}
            )
        self.assertEqual(request.state, "notified")
        self.assertFalse(request.signed_url_expires_at)

    def test_download_requires_a_signed_url(self):
        with self.assertRaises(UserError):
            self._new_request(state="requested")._download()

    def test_download_refuses_an_expired_url(self):
        request = self._new_request(
            state="notified",
            signed_url="https://storage.example.com/file.json",
            signed_url_expires_at=fields.Datetime.now() - timedelta(hours=1),
        )
        with self.assertRaises(UserError):
            request._download()

    def test_apply_requires_a_payload(self):
        with self.assertRaises(UserError):
            self._new_request(state="downloaded").action_apply()

    def test_transport_hooks_are_not_implemented_in_the_core(self):
        request = self._new_request(state="downloaded", payload="{}")
        with self.assertRaises(NotImplementedError):
            request.action_apply()
        with self.assertRaises(NotImplementedError):
            request._fetch_status()
        with self.assertRaises(NotImplementedError):
            request._fetch_payload()

    def test_second_reconcile_keeps_treated_divergences(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 130.0}})
        divergence.action_mark_handled()
        self._reconcile_against({"debit": {self._key(1): 130.0}})
        self.assertEqual(self.period.divergence_ids, divergence)
        self.assertEqual(divergence.state, "handled")
        self.assertEqual(self.period.state, "reconciled")

    def test_handled_divergences_then_reconcile_sets_reconciled(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {}})
        divergence.notes = "Accepted the assessed value without a local document."
        divergence.action_mark_ignored()
        self._reconcile_against({"debit": {}})
        self.assertEqual(self.period.state, "reconciled")
        self.assertEqual(self.period.divergence_ids.state, "ignored")

    def test_changed_amount_reopens_treated_divergence(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 130.0}})
        divergence.action_mark_handled()
        self._upsert_debits({self._key(1): 140.0})
        self._reconcile_against({"debit": {self._key(1): 130.0}})
        self.assertEqual(self.period.divergence_ids, divergence)
        self.assertEqual(divergence.state, "open")
        self.assertEqual(divergence.fisco_value, 140.0)
        self.assertEqual(self.period.state, "diverged")

    def test_increment_on_confirmed_period_keeps_state_and_schedules_activity(self):
        self._upsert_debits({self._key(1): 100.0})
        self._reconcile_against({"debit": {self._key(1): 100.0}})
        self.period.action_confirm()
        activities_before = self.period.activity_ids
        messages_before = self.period.message_ids
        self._upsert_debits({self._key(1): 120.0})
        self.assertEqual(self.period.state, "confirmed")
        self.assertEqual(self.period.fisco_debit, 120.0)
        self.assertEqual(len(self.period.activity_ids - activities_before), 1)
        self.assertTrue(self.period.message_ids - messages_before)

    def test_apply_without_data_returns_origin_to_draft(self):
        origin = self.period_model.create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "per_apur": "2026-09",
                "state": "requested",
            }
        )
        request = self._new_request(period_id=origin.id, payload="{}")
        messages_before = origin.message_ids
        parsed = {"2026-10": [{"document_key": self._key(1), "value": 100.0}]}
        with patch(f"{REQUEST_CLASS}._parse_payload", return_value=parsed):
            request._apply()
        self.assertEqual(origin.state, "draft")
        self.assertIn(self.period, request.period_ids)
        self.assertTrue(origin.message_ids - messages_before)

    def test_bookkeeping_awaits_download_until_both_directions_are_ready(self):
        self.assertTrue(self.period.local_awaiting_download)
        self._upsert_debits({self._key(1): 100.0})
        self.assertTrue(self.period.local_awaiting_download)
        self.period.no_credits = True
        self.assertFalse(self.period.local_awaiting_download)

    def test_request_name_uses_user_timezone(self):
        self.env.user.tz = "America/Sao_Paulo"
        request = self._new_request(
            request_date=fields.Datetime.from_string("2026-09-22 01:01:47")
        )
        self.assertIn("2026-09-21 22:01:47", request.name)

    def test_one_direction_does_not_make_the_period_ready(self):
        """The first answer must not look like both services arrived."""
        self._upsert_debits({self._key(1): 100.0})
        self.assertEqual(self.period.debit_delivery, "received")
        self.assertEqual(self.period.credit_delivery, "pending")
        self.assertFalse(self.period.directions_ready)

    def test_marking_a_direction_absent_unlocks_reconciliation(self):
        self._upsert_debits({self._key(1): 100.0})
        self.period.no_credits = True
        self.assertEqual(self.period.credit_delivery, "none")
        self.assertTrue(self.period.directions_ready)

    def test_open_request_marks_the_direction_in_progress(self):
        self._new_request(service="credits", state="notified", period_id=self.period.id)
        self.assertEqual(self.period.credit_delivery, "requested")
        self.assertFalse(self.period.directions_ready)

    def test_done_request_reports_only_what_it_delivered(self):
        request = self._new_request(payload="{}", period_id=self.period.id)
        parsed = {
            "2026-10": [
                {"document_key": self._key(1), "value": 80.0},
                {"document_key": self._key(2), "value": 40.0},
            ]
        }
        with patch(f"{REQUEST_CLASS}._parse_payload", return_value=parsed):
            request._apply()
            self.assertEqual(request.delivered_line_count, 2)
            self.assertEqual(request.delivered_amount, 120.0)
        self.assertEqual(self.period.debit_delivery, "received")

    def test_missing_local_cannot_be_handled_without_a_document(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {}})
        with self.assertRaises(UserError):
            divergence.action_mark_handled()
        self.assertEqual(divergence.state, "open")

    def test_missing_local_is_handled_when_the_document_is_linked(self):
        key = "35200159594315000157550010000000022062777169"
        self._upsert_debits({key: 100.0})
        divergence = self._reconcile_against({"debit": {}})
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_key": key,
            }
        )
        divergence.document_id = document
        divergence.action_mark_handled()
        self.assertEqual(divergence.state, "handled")

    def test_ignore_requires_a_note(self):
        self._upsert_debits({self._key(1): 100.0})
        divergence = self._reconcile_against({"debit": {self._key(1): 130.0}})
        with self.assertRaises(UserError):
            divergence.action_mark_ignored()
        divergence.notes = "The extra booked amount is a rounding of another period."
        divergence.action_mark_ignored()
        self.assertEqual(divergence.state, "ignored")

    def test_local_totals_include_both_directions_before_download(self):
        booked = {
            "debit": {self._key(1): 80.0},
            "credit": {self._key(3): 15.0},
        }
        with patch(
            f"{PERIOD_CLASS}._local_values_by_key", return_value=booked
        ) as mocked:
            self.period.invalidate_recordset(
                ["local_debit", "local_credit", "local_balance"]
            )
            self.assertEqual(self.period.local_debit, 80.0)
            self.assertEqual(self.period.local_credit, 15.0)
            self.assertEqual(self.period.local_balance, 65.0)
        args, kwargs = mocked.call_args
        line_types = kwargs.get("line_types") or args[-1]
        self.assertEqual(set(line_types), {"debit", "credit"})

    def test_absent_direction_reports_booked_documents_as_missing_fisco(self):
        self._upsert_debits({self._key(1): 100.0})
        self.period.no_credits = True
        divergences = self._reconcile_against(
            {"debit": {self._key(1): 100.0}, "credit": {self._key(3): 15.0}}
        )
        missing = divergences.filtered(
            lambda line: line.divergence_type == "missing_fisco"
        )
        self.assertEqual(missing.line_type, "credit")
        self.assertEqual(missing.document_key, self._key(3))
        self.assertEqual(missing.local_value, 15.0)

    def test_bookkeeping_status_waits_until_the_direction_can_be_compared(self):
        self.assertEqual(
            self.period._bookkeeping_status("credit", 15.0, None, {"debit"}),
            "awaiting",
        )
        self.assertEqual(
            self.period._bookkeeping_status("credit", 15.0, None, {"credit"}),
            "only_erp",
        )
        self.assertEqual(
            self.period._bookkeeping_status("credit", 15.0, 15.0, {"credit"}),
            "match",
        )
        self.assertEqual(
            self.period._bookkeeping_status("credit", 15.0, 10.0, {"credit"}),
            "value",
        )
