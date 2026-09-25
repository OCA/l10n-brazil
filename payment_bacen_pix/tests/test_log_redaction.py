# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.payment_bacen_pix.utils import redact_personal_data

from .common import (
    PROVIDER_PATH,
    TRANSACTION_PATH,
    ApiResponse,
    BacenPixCommon,
    collect_logs,
)


@tagged("post_install", "-at_install")
class TestBacenPixLogRedaction(BacenPixCommon):
    """A charge carries the name and the document of the payer: keep them out
    of the log."""

    def test_redact_drops_the_document_and_the_name(self):
        redacted = redact_personal_data(
            {
                "devedor": {
                    "cnpj": "11222333000181",
                    "nome": "Cliente Pix",
                    "logradouro": "Rua das Flores, 100",
                    "cep": "37540000",
                },
                "valor": {"original": "100.00"},
            }
        )
        self.assertNotIn("11222333000181", str(redacted))
        self.assertNotIn("Cliente Pix", str(redacted))
        self.assertNotIn("Rua das Flores", str(redacted))
        self.assertEqual(redacted["valor"], {"original": "100.00"})

    def test_redact_walks_through_the_lists_of_payments(self):
        """The `pix` list of a charge holds the payer of every payment."""
        redacted = redact_personal_data(
            {"pix": [{"pagador": {"cpf": "12345678909", "nome": "Fulano"}}]}
        )
        self.assertNotIn("12345678909", str(redacted))
        self.assertNotIn("Fulano", str(redacted))

    def test_failed_request_does_not_log_the_payer(self):
        """A 4xx from the PSP must not turn the payload into a log entry."""
        self.partner.write({"vat": "11.222.333/0001-81", "name": "Cliente Pix"})
        transaction = self.env["payment.transaction"].create(
            {
                "provider_id": self.bacenpix.id,
                "reference": "LOG-0001",
                "amount": 10.0,
                "currency_id": self.currency_brl.id,
                "partner_id": self.partner.id,
            }
        )
        response = ApiResponse(
            {"title": "erro"},
            status_code=400,
            raises=requests.exceptions.HTTPError("HTTP 400"),
        )
        with collect_logs(f"{PROVIDER_PATH}") as records:
            with patch(
                f"{PROVIDER_PATH}.requests.request", return_value=response
            ), patch(
                f"{PROVIDER_PATH}.PaymentProvider._bacenpix_get_token",
                return_value="token",
            ):
                with self.assertRaises(ValidationError):
                    transaction._bacenpix_create_charge()

        logged = "\n".join(records)
        self.assertIn("invalid API request", logged)
        self.assertNotIn("11222333000181", logged, "the document reached the log")
        self.assertNotIn("Cliente Pix", logged, "the name reached the log")

    def test_charge_response_is_logged_without_the_payer(self):
        """The response of the PSP echoes the debtor back."""
        transaction = self.env["payment.transaction"].create(
            {
                "provider_id": self.bacenpix.id,
                "reference": "LOG-0002",
                "amount": 10.0,
                "currency_id": self.currency_brl.id,
                "partner_id": self.partner.id,
            }
        )
        response = self._charge_response(
            devedor={"cnpj": "11222333000181", "nome": "Cliente Pix"}
        )
        with collect_logs(TRANSACTION_PATH) as records:
            with self._patch_request(response=response):
                transaction._bacenpix_create_charge()

        logged = "\n".join(records)
        self.assertIn("charge creation response", logged)
        self.assertNotIn("11222333000181", logged, "the document reached the log")
        self.assertNotIn("Cliente Pix", logged, "the name reached the log")
