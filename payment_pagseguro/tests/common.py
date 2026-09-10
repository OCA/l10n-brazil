# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.payment.tests.common import PaymentCommon


class PagseguroCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.currency_brl = cls._prepare_currency("BRL")
        cls.pagseguro = cls._prepare_provider(
            "pagseguro",
            update_values={
                "pagseguro_token": "dummy-token",
                "pagseguro_soft_descriptor": "Odoo Community Association",
            },
        )

        cls.provider = cls.pagseguro
        cls.currency = cls.currency_brl

        cls.encrypted_card = "encrypted-card-payload"
        cls.card_holder = "Norbert Buyer"
        cls.card_id = "CARD_9d5c9c9c-0e5b-4b8e-8d6f-6f8a5b0c9d1e"
        cls.charge_id = "CHAR_1f4b6a2c-7b3e-4a1d-9c2f-8e7d6c5b4a39"

    @classmethod
    def _order_response(cls, status="PAID", store=False, **charge_values):
        """Return a response of PagBank to an order request."""
        return {
            "id": "ORDE_3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
            "reference_id": cls.reference,
            "charges": [cls._charge_response(status, store, **charge_values)],
        }

    @classmethod
    def _charge_response(cls, status="PAID", store=False, **values):
        """Return a charge as answered by PagBank."""
        card = {"brand": "visa", "last_digits": "2931"}
        if store:
            card["id"] = cls.card_id
        return {
            "id": cls.charge_id,
            "reference_id": cls.reference,
            "status": status,
            "payment_response": {"code": "20000", "message": "SUCESSO"},
            "payment_method": {"type": "CREDIT_CARD", "installments": 1, "card": card},
            **values,
        }

    @contextmanager
    def _patch_request(self, response=None, responses=None):
        """Patch the requests made to PagBank and record the calls."""
        with patch(
            "odoo.addons.payment_pagseguro.models.payment_provider.PaymentProvider"
            "._pagseguro_make_request",
            return_value=response if responses is None else None,
            side_effect=responses,
        ) as request_mock:
            yield request_mock
