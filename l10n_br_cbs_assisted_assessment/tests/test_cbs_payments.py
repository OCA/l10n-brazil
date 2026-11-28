# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import CLIENT_CLASS

CBS_REQUEST_LOG = (
    "odoo.addons.l10n_br_cbs_assisted_assessment.models.assisted_assessment_request"
)
# NF-e key accepted by l10n_br_fiscal_edi (model 55 and a valid check digit).
# A zero-padded key is rejected once that module is installed with the suite.
DOCUMENT_KEY = "35260811222333000181550010000000011317534953"
PERIOD_CLASS = (
    "odoo.addons.l10n_br_assisted_assessment.models.assisted_assessment"
    ".AssistedAssessment"
)


def _payments_file(principal=100.0, keep_second=True):
    composition = [
        {
            "sequencial": 1,
            "pa": "08/2026",
            "vencimento": "2026-09-20",
            "niContribuinte": "11222333000181",
            "chaveDFE": DOCUMENT_KEY,
            "principal": principal,
            "multa": 1,
            "juros": 2,
            "total": principal + 3,
        }
    ]
    if keep_second:
        composition.append(
            {
                "sequencial": 2,
                "pa": "07/2026",
                "vencimento": "2026-08-20",
                "niContribuinte": "11222333000181",
                "principal": 5,
                "total": 5,
            }
        )
    return {
        "apuracao": [
            {
                "dataArrecadacao": "2026-08-15",
                "pagamentos": [
                    {
                        "numeroDARF": "12345678901234567",
                        "tipo": 1,
                        "niAdquirente": "99888777000166",
                        "composicao": composition,
                    },
                    {
                        "numeroDARF": "12345678901234568",
                        "tipo": 2,
                        "niContribuinte": "11222333000181",
                        "composicao": [
                            {
                                "sequencial": 1,
                                "pa": "08/2026",
                                "vencimento": "2026-09-20",
                                "principal": 40,
                                "total": 40,
                            }
                        ],
                    },
                ],
            }
        ]
    }


WITHHOLDINGS_FILE = {
    "apuracao": [
        {
            "dataArrecadacao": "2026-08-15",
            "pagamentos": [
                {
                    "numeroDARF": "12345678901234569",
                    "tipo": 1,
                    "composicao": [
                        {
                            "sequencial": 1,
                            "pa": "08/2026",
                            "vencimento": "2026-09-20",
                            "niFornecedor": "55444333000122",
                            "chaveDFE": DOCUMENT_KEY,
                            "principal": 15,
                            "total": 15,
                        }
                    ],
                }
            ],
        }
    ]
}


class TestCbsPayments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.request_model = cls.env["l10n_br_assisted_assessment.request"]
        cls.period_model = cls.env["l10n_br_assisted_assessment.period"]
        cls.payment_model = cls.env["l10n_br_cbs_assisted_assessment.payment"]

    def _new_request(self, service="payments", **vals):
        return self.request_model.create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "service": service,
                **vals,
            }
        )

    def _document(self, key):
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_key": key,
                "document_date": "2026-08-01",
                "fiscal_operation_type": "in",
            }
        )

    def test_parse_payments_reads_rad_and_pcont(self):
        request = self._new_request(payload=json.dumps(_payments_file()))
        parsed = request._parse_payment_payload()
        self.assertEqual(len(parsed), 2)
        rad, pcont = parsed
        self.assertEqual(rad["payment_type"], "1")
        self.assertEqual(rad["counterparty_vat"], "99888777000166")
        self.assertEqual(rad["lines"][0]["document_key"], DOCUMENT_KEY)
        self.assertEqual(rad["lines"][0]["counterparty_vat"], "11222333000181")
        self.assertEqual(pcont["payment_type"], "2")
        self.assertEqual(pcont["counterparty_vat"], "11222333000181")
        self.assertFalse(pcont["lines"][0]["document_key"])

    def test_parse_withholdings_reads_the_supplier(self):
        request = self._new_request(
            service="withholdings", payload=json.dumps(WITHHOLDINGS_FILE)
        )
        parsed = request._parse_payment_payload()
        self.assertEqual(len(parsed), 1)
        self.assertFalse(parsed[0]["counterparty_vat"])
        self.assertEqual(parsed[0]["lines"][0]["counterparty_vat"], "55444333000122")
        self.assertEqual(parsed[0]["lines"][0]["per_apur"], "2026-08")

    def test_apply_payments_upserts_and_keeps_the_period_state(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-08")
        period.state = "received"
        document = self._document(DOCUMENT_KEY)
        request = self._new_request(
            state="downloaded",
            payload=json.dumps(_payments_file()),
            period_id=period.id,
        )
        request._apply()
        self.assertEqual(request.state, "done")
        self.assertEqual(period.state, "received")
        self.assertFalse(period.line_ids)
        rad = self.payment_model.search(
            [
                ("company_id", "=", self.company.id),
                ("service", "=", "payments"),
                ("payment_type", "=", "1"),
            ]
        )
        self.assertEqual(len(rad), 1)
        self.assertEqual(rad.counterparty_vat, "99888777000166")
        matched = rad.line_ids.filtered(lambda line: line.sequence == 1)
        self.assertEqual(matched.document_id, document)
        self.assertEqual(matched.amount_total, 103)
        self.assertIn(period, request.period_ids)
        self.assertEqual(period.payment_delivery, "received")
        self.assertEqual(period.withholding_delivery, "pending")
        july = self.period_model._get_or_create(self.company, "cbs", "2026-07")
        self.assertEqual(july.state, "draft")
        self.assertEqual(july.payment_delivery, "received")

        updated = self._new_request(
            state="downloaded",
            payload=json.dumps(_payments_file(principal=200.0, keep_second=False)),
        )
        updated._apply()
        rad.invalidate_recordset()
        self.assertEqual(
            self.payment_model.search_count(
                [
                    ("company_id", "=", self.company.id),
                    ("darf_number", "=", "12345678901234567"),
                ]
            ),
            1,
        )
        self.assertEqual(len(rad.line_ids), 2)
        self.assertEqual(
            rad.line_ids.filtered(lambda line: line.sequence == 1).amount_principal,
            200,
        )
        self.assertEqual(
            rad.line_ids.filtered(lambda line: line.sequence == 2).amount_total,
            5,
        )
        self.assertEqual(rad.request_id, updated)

    def test_payment_delivery_follows_the_open_request(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-09")
        self.assertEqual(period.payment_delivery, "pending")
        self.assertEqual(period.withholding_delivery, "pending")
        payment = self._new_request(
            service="payments", state="requested", period_id=period.id
        )
        self.assertEqual(period.payment_delivery, "requested")
        self.assertEqual(period.withholding_delivery, "pending")
        self._new_request(service="withholdings", state="notified", period_id=period.id)
        self.assertEqual(period.withholding_delivery, "requested")
        payment.state = "error"
        self.assertEqual(period.payment_delivery, "pending")

    def test_a_new_payment_request_reopens_a_delivered_service(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-08")
        done = self._new_request(service="payments", state="done", period_id=period.id)
        done.period_ids = period
        self.assertEqual(period.payment_delivery, "received")
        again = self._new_request(
            service="payments", state="requested", period_id=period.id
        )
        self.assertEqual(period.payment_delivery, "requested")
        again.state = "error"
        self.assertEqual(period.payment_delivery, "received")

    def test_open_payment_request_blocks_the_same_service_only(self):
        period = self.period_model._get_or_create(self.company, "cbs", "2026-09")
        self._new_request(service="payments", state="requested")
        with self.assertRaises(UserError):
            period.action_request_payments()
        answer = {"tiqueteSolicitacao": "ticket", "tEASegundos": "1"}
        with patch(f"{CLIENT_CLASS}._open_request", return_value=answer):
            withholding = period.action_request_withholdings()
        self.assertEqual(withholding.service, "withholdings")
        self.assertEqual(withholding.state, "requested")

    def test_daily_cron_opens_every_service(self):
        with patch(f"{PERIOD_CLASS}._create_request", return_value=True) as created:
            self.request_model._cron_request_daily()
        # The patched method is a mock, so the recordset is not bound as args[0].
        services = [call.args[-1] for call in created.call_args_list]
        self.assertEqual(services, ["debits", "credits", "payments", "withholdings"])
