# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from contextlib import contextmanager
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.l10n_br_cbs_assisted_assessment_mock.models.mock_file import (
    SAMPLE_AMOUNT,
    SAMPLE_KEY,
)

REQUESTS = (
    "odoo.addons.l10n_br_cbs_assisted_assessment.models.receita_integra_rtc.requests"
)
REQUEST_LOG = (
    "odoo.addons.l10n_br_cbs_assisted_assessment.models.assisted_assessment_request"
)


class TestCbsAssessmentMock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mute = mute_logger(REQUEST_LOG)
        mute.__enter__()
        cls.addClassCleanup(lambda: mute.__exit__(None, None, None))
        cls.company = cls.env.company
        cls.company.write(
            {
                "cbs_assessment_mock_mode": True,
                "cbs_assessment_client_id": False,
                "cbs_assessment_client_secret": False,
            }
        )
        cls.period_model = cls.env["l10n_br_assisted_assessment.period"]
        cls.file_model = cls.env["l10n_br_cbs_assisted_assessment.mock.file"]
        cls.payment_model = cls.env["l10n_br_cbs_assisted_assessment.payment"]

    def _current_period(self):
        today = fields.Date.context_today(self.file_model)
        per_apur = f"{today.year:04d}-{today.month:02d}"
        return self.period_model._get_or_create(self.company, "cbs", per_apur)

    @contextmanager
    def _block_http(self):
        def refuse(*args, **kwargs):
            raise AssertionError("The mock reached the Receita Federal")

        with (
            patch(f"{REQUESTS}.post", side_effect=refuse),
            patch(f"{REQUESTS}.request", side_effect=refuse),
            patch(f"{REQUESTS}.get", side_effect=refuse),
        ):
            yield

    def _finish(self, request):
        request.action_check_status()
        self.assertEqual(request.state, "notified")
        self.assertTrue(request.signed_url.startswith("mock://"))
        request.action_download()
        request.action_apply()
        self.assertEqual(request.state, "done")

    def test_empty_period_uses_a_sample_line(self):
        period = self._current_period()
        payload = self.file_model._build_payload(period, "debits")
        items = payload["apuracao"][0]["debitos"]
        if period._local_document_lines(["debit"]):
            self.assertTrue(items)
        else:
            self.assertEqual(items[0]["chave"], SAMPLE_KEY)
            self.assertEqual(items[0]["cbs"]["apurado"], SAMPLE_AMOUNT)
            self.assertTrue(items[0]["emissao"].startswith(period.per_apur))

    def test_sample_line_stays_inside_an_older_period(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-10")
        item = self.file_model._sample_item(period, credit=True)
        self.assertTrue(item["emissao"].startswith("2026-10-"))
        self.assertEqual(item["registro"], item["emissao"])
        self.assertEqual(item["atualizacao"], item["emissao"])

    def test_payment_collection_stays_inside_the_period(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-10")
        for service in ("payments", "withholdings"):
            payload = self.file_model._build_payload(period, service)
            assessment = payload["apuracao"][0]
            self.assertEqual(assessment["dataArrecadacao"], "2026-10-15")
            due = assessment["pagamentos"][0]["composicao"][0]["vencimento"]
            self.assertEqual(due, fields.Date.to_string(period.date_deadline))
            self.assertTrue(due.startswith("2026-11-"))

    def test_prepared_file_is_served(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-08")
        self.file_model.create(
            {
                "company_id": self.company.id,
                "service": "debits",
                "period_id": period.id,
                "payload": json.dumps(
                    {
                        "apuracao": [
                            {
                                "pa": "08/2026",
                                "debitos": [
                                    {
                                        "origem": 0,
                                        "documento": 55,
                                        "chave": SAMPLE_KEY,
                                        "emissao": "2026-08-01T00:00:00Z",
                                        "registro": "2026-08-01T00:00:00Z",
                                        "atualizacao": "2026-08-01T00:00:00Z",
                                        "cbs": {
                                            "apurado": 42,
                                            "saldoDevedor": 42,
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                ),
            }
        )
        with self._block_http():
            request = period.action_request_debits()
            self.assertTrue(request.ticket.startswith("MOCK-"))
            self._finish(request)
        self.assertEqual(
            period.line_ids.filtered(
                lambda line: line.document_key == SAMPLE_KEY
            ).value,
            42,
        )

    def test_request_payments_keeps_the_period_state(self):
        period = self._current_period()
        with self._block_http():
            request = period.action_request_payments()
            self._finish(request)
        self.assertEqual(period.state, "requested")
        payments = self.payment_model.search([("request_id", "=", request.id)])
        self.assertEqual(set(payments.mapped("payment_type")), {"1", "2"})

    def test_wizard_replaces_the_waiting_draft(self):
        period = self._current_period()
        wizard = self.env["l10n_br_cbs_assisted_assessment.mock.generate"].create(
            {
                "company_id": self.company.id,
                "period_id": period.id,
                "credits": False,
                "payments": False,
                "withholdings": False,
            }
        )
        wizard.action_generate()
        wizard.action_generate()
        drafts = self.file_model.search(
            [
                ("company_id", "=", self.company.id),
                ("service", "=", "debits"),
                ("state", "=", "draft"),
            ]
        )
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts.period_id, period)

    def test_unprepared_request_stays_in_the_period_it_was_opened_from(self):
        today = fields.Date.context_today(self.file_model)
        current = f"{today.year:04d}-{today.month:02d}"
        other = "2026-01" if current != "2026-01" else "2026-02"
        period = self.period_model._get_or_create(self.company, "cbs", other)
        with self._block_http():
            request = period.action_request_credits()
            self._finish(request)
        self.assertEqual(request.period_ids.mapped("per_apur"), [other])
        self.assertFalse(
            self.period_model.search(
                [
                    ("company_id", "=", self.company.id),
                    ("tribute", "=", "cbs"),
                    ("per_apur", "=", current),
                ]
            )
        )

    def test_draft_is_not_served_to_another_period(self):
        august = self.period_model._get_or_create(self.company, "cbs", "2026-08")
        september = self.period_model._get_or_create(self.company, "cbs", "2026-09")
        wizard = self.env["l10n_br_cbs_assisted_assessment.mock.generate"].create(
            {
                "company_id": self.company.id,
                "period_id": august.id,
                "credits": False,
                "payments": False,
                "withholdings": False,
            }
        )
        wizard.action_generate()
        with self._block_http():
            request = september.action_request_debits()
            self._finish(request)
        self.assertIn('"pa": "09/2026"', request.payload)
        self.assertEqual(
            self.file_model.search_count(
                [
                    ("company_id", "=", self.company.id),
                    ("service", "=", "debits"),
                    ("state", "=", "draft"),
                    ("period_id", "=", august.id),
                ]
            ),
            1,
        )

    def test_period_toggle_writes_the_company(self):
        self.company.cbs_assessment_mock_mode = False
        period = self._current_period()
        period.cbs_assessment_mock_mode = True
        self.assertTrue(self.company.cbs_assessment_mock_mode)

    def test_mock_off_does_not_serve_a_local_file(self):
        self.company.cbs_assessment_mock_mode = False
        period = self._current_period()
        with self.assertRaises(UserError):
            period.action_request_debits()
        self.assertFalse(self.file_model.search([("company_id", "=", self.company.id)]))
