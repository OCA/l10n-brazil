# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.payment.tests.common import PaymentCommon


class BacenPixCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.currency_brl = cls._prepare_currency("BRL")
        cls.bacenpix = cls._prepare_provider(
            "bacenpix",
            update_values={
                "bacenpix_psp": "bb",
                "bacenpix_key": "pix-key@example.com",
                "bacenpix_client_id": "dummy-client-id",
                "bacenpix_client_secret": "dummy-client-secret",
                "bacenpix_app_key": "dummy-app-key",
                "bacenpix_expiration": 3600,
            },
        )

        cls.provider = cls.bacenpix
        cls.currency = cls.currency_brl

        cls.txid = "9d36b84fc70b478fb95c12729b90ca25"
        cls.qr_code = (
            "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-42665544"
            "00005204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***63041D3D"
        )
        cls.end_to_end_id = "E1204567220200812150000123456789"

    @classmethod
    def _charge_response(cls, status="ATIVA", with_payment=False, **values):
        """Return a charge as answered by the Pix API."""
        response = {
            "calendario": {"criacao": "2026-07-27T20:00:00.000Z", "expiracao": 3600},
            "txid": cls.txid,
            "revisao": 0,
            "loc": {
                "id": 7716,
                "location": f"pix.example.com/qr/v2/{cls.txid}",
                "tipoCob": "cob",
            },
            "location": f"pix.example.com/qr/v2/{cls.txid}",
            "status": status,
            "valor": {"original": "1111.11"},
            "chave": "pix-key@example.com",
            "solicitacaoPagador": cls.reference,
            "pixCopiaECola": cls.qr_code,
            **values,
        }
        if with_payment:
            response["pix"] = [
                {
                    "endToEndId": cls.end_to_end_id,
                    "txid": cls.txid,
                    "valor": "1111.11",
                    "horario": "2026-07-27T20:05:00.000Z",
                }
            ]
        return response

    @contextmanager
    def _patch_request(self, response=None, responses=None):
        """Patch the requests made to the Pix API and record the calls."""
        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.PaymentProvider"
            "._bacenpix_make_request",
            return_value=response if responses is None else None,
            side_effect=responses,
        ) as request_mock:
            yield request_mock
