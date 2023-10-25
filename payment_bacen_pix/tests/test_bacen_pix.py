# Copyright 2023 KMEE
# License MIT - See https://opensource.org/license/mit

import os
from datetime import datetime

import vcr

import odoo


@odoo.tests.tagged("post_install", "-at_install")
class BacenCommon(odoo.tests.HttpCase):
    def setUp(self):
        super().setUp()

        bacenpix_client_id = "test_client_id"
        bacenpix_client_secret = "test_client_secret"
        bacenpix_basic = "test_client_basic"

        self.bacen = self.env["payment.acquirer"].create(
            {
                "name": "Bacen (pix)",
                "provider": "bacenpix",
                "bacenpix_email_account": "test@example.com",
                "bacen_pix_key": "7f6844d0-de89-47e5-9ef7-e0a35a681615",
                "bacenpix_client_id": bacenpix_client_id,
                "bacenpix_client_secret": bacenpix_client_secret,
                "bacenpix_dev_app_key": "7415558232312afe7fb3ccf1e0508aef",
                "bacen_pix_basic": bacenpix_basic,
                "bacenpix_api_key": "",
            }
        )

        self.bacen.write(
            {
                "state": "test",
            }
        )


class BacenTest(BacenCommon):
    @vcr.use_cassette(
        os.path.dirname(__file__) + "/fixtures/test_pix_bacen.yaml",
        match_on=["method", "scheme", "host", "port", "path", "query", "body"],
        ignore_localhost=True,
    )
    def test_bacen_pix(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Francisco da Silva",
                "email": "test@partner.com",
                "cnpj_cpf": "123.456.789-09",
            }
        )

        tx = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.bacen.id,
                "partner_id": partner.id,
                "bacenpix_date_due": datetime.now(),
                "bacenpix_currency": "BRL",
                "bacenpix_amount": 42.42,
                "partner_name": partner.name,
                "bacenpix_txid": 12345678909,
                "amount": "123.45",
            }
        )

        self.assertEqual(tx.state_message, 0)

    def test_bacen_pix_fail_token(self):
        self.bacen.bacen_pix_get_token()
        self.assertEqual(self.bacen.bacenpix_api_key, "Error")


class TestBacenWebhook(odoo.tests.HttpCase):
    def test_bacenpix_webhook(self):
        tx_reference = {"reference": 12345678909}

        response = self.url_open(
            "/webhook/%s" % tx_reference,
            data=tx_reference,
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 400)

    def test_transfer_form_feedback(self):
        tx_reference = {"reference": 12345678909}
        response = self.url_open("/payment/bacenpix/feedback", data=tx_reference)
        self.assertEqual(response.status_code, 200)
