# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.payment.tests.common import PaymentCommon


class CieloCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.currency_brl = cls._prepare_currency("BRL")
        cls.cielo = cls._prepare_provider(
            "cielo",
            update_values={
                "cielo_merchant_id": "12345678-1234-1234-1234-123456789012",
                "cielo_merchant_key": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123",
                "cielo_soft_descriptor": "Odoo Community",
            },
        )

        cls.provider = cls.cielo
        cls.currency = cls.currency_brl

        cls.card_data = {
            "card_number": "4024 0071 9769 2931",
            "card_holder": "Norbert Buyer",
            "card_expiry": "02/30",
            "card_verification_code": "123",
        }
        cls.card_token = "905ffdbd-ddc1-49f5-b9b8-9e512ba9917e"
        cls.payment_id = "24bc8901-9c3f-4a1c-92db-1d17c1a3c9f6"

    @classmethod
    def _sale_response(cls, status=2, save_card=False, **payment_values):
        """Return a response of Cielo to a sale request."""
        credit_card = {
            "CardNumber": "402400******2931",
            "Holder": "Norbert Buyer",
            "ExpirationDate": "02/2030",
            "Brand": "Visa",
            "SaveCard": save_card,
        }
        if save_card:
            credit_card["CardToken"] = cls.card_token
        return {
            "MerchantOrderId": cls.reference,
            "Customer": {"Name": "Norbert Buyer"},
            "Payment": {
                "PaymentId": cls.payment_id,
                "Type": "CreditCard",
                "Amount": 111111,
                "Installments": 1,
                "Status": status,
                "ReturnCode": "4",
                "ReturnMessage": "Operation Successful",
                "CreditCard": credit_card,
                **payment_values,
            },
        }

    @classmethod
    def _operation_response(cls, status=2, **values):
        """Return a response of Cielo to a capture or void request."""
        return {
            "Status": status,
            "ReasonCode": 0,
            "ReasonMessage": "Successful",
            "ProviderReturnCode": "6",
            **values,
        }

    @contextmanager
    def _patch_request(self, response=None, responses=None):
        """Patch the requests made to Cielo and record the calls.

        :param dict response: The content returned by every request.
        :param list responses: The contents returned by the successive requests.
        :return: The mock of `_cielo_make_request`.
        """
        with patch(
            "odoo.addons.payment_cielo.models.payment_provider.PaymentProvider"
            "._cielo_make_request",
            return_value=response if responses is None else None,
            side_effect=responses,
        ) as request_mock:
            yield request_mock
