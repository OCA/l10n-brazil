# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from .common import PagseguroCommon

_TX_LOGGER = "odoo.addons.payment.models.payment_transaction"
_PAGSEGURO_LOGGER = "odoo.addons.payment_pagseguro.models.payment_transaction"


@tagged("post_install", "-at_install")
class TestPagseguroPaymentFlows(PagseguroCommon):
    def test_direct_payment_sends_an_order(self):
        """The encrypted card is forwarded to PagBank in an order."""
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._order_response()) as request_mock:
            tx._pagseguro_create_order(
                encrypted_card=self.encrypted_card, card_holder=self.card_holder
            )

        endpoint, payload = request_mock.call_args.args
        self.assertEqual(endpoint, "/orders")
        self.assertEqual(payload["reference_id"], self.reference)
        self.assertEqual(payload["customer"]["name"], self.partner.name)
        charge = payload["charges"][0]
        self.assertEqual(charge["amount"], {"value": 111111, "currency": "BRL"})
        payment_method = charge["payment_method"]
        self.assertEqual(payment_method["type"], "CREDIT_CARD")
        self.assertTrue(payment_method["capture"])
        self.assertEqual(payment_method["card"]["encrypted"], self.encrypted_card)
        self.assertEqual(payment_method["card"]["holder"]["name"], self.card_holder)
        self.assertFalse(payment_method["card"]["store"])

    def test_soft_descriptor_is_truncated(self):
        """PagBank rejects soft descriptors longer than 17 characters."""
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._order_response()) as request_mock:
            tx._pagseguro_create_order(encrypted_card=self.encrypted_card)

        charge = request_mock.call_args.args[1]["charges"][0]
        self.assertEqual(
            charge["payment_method"]["soft_descriptor"], "Odoo Community Ass"[:17]
        )

    def test_manual_capture_only_authorizes_the_charge(self):
        """The charge is not captured along with the order."""
        self.pagseguro.capture_manually = True
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._order_response("AUTHORIZED")) as request_mock:
            tx._pagseguro_create_order(encrypted_card=self.encrypted_card)

        charge = request_mock.call_args.args[1]["charges"][0]
        self.assertFalse(charge["payment_method"]["capture"])

    def test_payment_without_card_nor_token_is_rejected(self):
        """A payment with neither card nor token never reaches PagBank."""
        tx = self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            tx._pagseguro_prepare_card_payload()

    def test_payment_by_token_uses_the_saved_card(self):
        """A payment made with a token sends the card id saved by PagBank."""
        token = self._create_token(provider_ref=self.card_id)
        tx = self._create_transaction(flow="token", token_id=token.id)
        with self._patch_request(self._order_response()) as request_mock, mute_logger(
            _TX_LOGGER
        ):
            tx._send_payment_request()

        charge = request_mock.call_args.args[1]["charges"][0]
        self.assertEqual(charge["payment_method"]["card"], {"id": self.card_id})
        self.assertEqual(tx.state, "done")

    def test_tokenization_saves_the_card(self):
        """PagBank returns a card id that is saved when the customer asks."""
        tx = self._create_transaction(flow="direct", tokenize=True)
        with self._patch_request(self._order_response(store=True)) as request_mock:
            tx._pagseguro_create_order(encrypted_card=self.encrypted_card)
        charge = request_mock.call_args.args[1]["charges"][0]
        self.assertTrue(charge["payment_method"]["card"]["store"])

        tx._handle_notification_data(
            "pagseguro", {"response": self._order_response(store=True)}
        )

        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.token_id.provider_ref, self.card_id)
        self.assertEqual(tx.token_id.payment_details, "2931")
        self.assertEqual(tx.token_id.pagseguro_card_brand, "visa")
        self.assertFalse(tx.tokenize)

    @mute_logger(_PAGSEGURO_LOGGER)
    def test_no_token_is_created_without_a_card_id(self):
        """No token is created when PagBank does not save the card."""
        tx = self._create_transaction(flow="direct", tokenize=True)
        tx._handle_notification_data("pagseguro", {"response": self._order_response()})

        self.assertEqual(tx.state, "done")
        self.assertFalse(tx.token_id)

    def test_transaction_is_found_from_the_reference_id(self):
        """The reference sent back by PagBank identifies the transaction."""
        tx = self._create_transaction(flow="direct")
        found_tx = self.env["payment.transaction"]._get_tx_from_notification_data(
            "pagseguro", {"response": self._order_response()}
        )
        self.assertEqual(found_tx, tx)

    def test_unknown_reference_is_rejected(self):
        """A notification that matches no transaction is rejected."""
        self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._get_tx_from_notification_data(
                "pagseguro", {"reference": "no-such-reference"}
            )


@tagged("post_install", "-at_install")
class TestPagseguroNotificationData(PagseguroCommon):
    def _process(self, status, **kwargs):
        tx = self._create_transaction(flow="direct", **kwargs)
        tx._handle_notification_data(
            "pagseguro", {"response": self._order_response(status)}
        )
        return tx

    def test_paid_charge_sets_the_transaction_done(self):
        tx = self._process("PAID")
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, self.charge_id)

    def test_authorized_charge_sets_the_transaction_authorized(self):
        self.pagseguro.capture_manually = True
        tx = self._process("AUTHORIZED")
        self.assertEqual(tx.state, "authorized")

    def test_waiting_charge_sets_the_transaction_pending(self):
        for status in ("WAITING", "IN_ANALYSIS"):
            self.reference = f"Test Transaction {status}"
            tx = self._process(status)
            self.assertEqual(tx.state, "pending")

    @mute_logger(_PAGSEGURO_LOGGER)
    def test_declined_charge_sets_the_transaction_in_error(self):
        tx = self._process("DECLINED")
        self.assertEqual(tx.state, "error")
        self.assertIn("SUCESSO", tx.state_message)

    def test_canceled_charge_cancels_the_transaction(self):
        tx = self._process("CANCELED")
        self.assertEqual(tx.state, "cancel")

    @mute_logger(_PAGSEGURO_LOGGER)
    def test_unknown_status_sets_the_transaction_in_error(self):
        tx = self._process("SOMETHING_ELSE")
        self.assertEqual(tx.state, "error")

    def test_missing_charge_is_rejected(self):
        tx = self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            tx._handle_notification_data("pagseguro", {"response": {}})

    def test_missing_status_is_rejected(self):
        tx = self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            tx._handle_notification_data(
                "pagseguro", {"response": {"charges": [{"id": self.charge_id}]}}
            )


@tagged("post_install", "-at_install")
class TestPagseguroOperations(PagseguroCommon):
    def setUp(self):
        super().setUp()
        self.pagseguro.capture_manually = True

    def test_capture_request(self):
        """The authorized charge is captured for the amount of the transaction."""
        tx = self._create_transaction(
            flow="direct", state="authorized", provider_reference=self.charge_id
        )
        with self._patch_request(self._charge_response("PAID")) as request_mock:
            tx._send_capture_request()

        endpoint, payload = request_mock.call_args.args
        self.assertEqual(endpoint, f"/charges/{self.charge_id}/capture")
        self.assertEqual(payload["amount"], {"value": 111111, "currency": "BRL"})
        self.assertEqual(tx.state, "done")

    def test_void_request(self):
        """The authorized charge is canceled in full."""
        tx = self._create_transaction(
            flow="direct", state="authorized", provider_reference=self.charge_id
        )
        with self._patch_request(self._charge_response("CANCELED")) as request_mock:
            tx._send_void_request()

        self.assertEqual(
            request_mock.call_args.args[0], f"/charges/{self.charge_id}/cancel"
        )
        self.assertIsNone(request_mock.call_args.args[1])
        self.assertEqual(tx.state, "cancel")

    @mute_logger(_TX_LOGGER)
    def test_refund_request(self):
        """A captured charge is refunded through the cancel endpoint."""
        tx = self._create_transaction(
            flow="direct", state="done", provider_reference=self.charge_id
        )
        with self._patch_request(self._charge_response("CANCELED")) as request_mock:
            refund_tx = tx._send_refund_request()

        endpoint, payload = request_mock.call_args.args
        self.assertEqual(endpoint, f"/charges/{self.charge_id}/cancel")
        self.assertEqual(payload["amount"]["value"], 111111)
        self.assertEqual(refund_tx.operation, "refund")
        self.assertEqual(refund_tx.state, "done")

    def test_validation_is_authorized_then_canceled(self):
        """Saving a card authorizes an amount and cancels it right away."""
        tx = self._create_transaction(flow="direct", operation="validation")
        with self._patch_request(self._charge_response("CANCELED")):
            tx._handle_notification_data(
                "pagseguro", {"response": self._order_response("AUTHORIZED")}
            )

        self.assertEqual(tx.state, "done")


@tagged("post_install", "-at_install")
class TestPagseguroController(PagseguroCommon, PaymentHttpCommon):
    def test_payment_route_processes_the_payment(self):
        """The payment route forwards the card and processes the response."""
        tx = self._create_transaction(flow="direct")
        url = self._build_url("/payment/pagseguro/payment")
        with self._patch_request(self._order_response()):
            self._make_json_rpc_request(
                url,
                data={
                    "reference": tx.reference,
                    "partner_id": self.partner.id,
                    "access_token": self._generate_test_access_token(
                        tx.reference, self.partner.id
                    ),
                    "encrypted_card": self.encrypted_card,
                    "card_holder": self.card_holder,
                },
            )

        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, self.charge_id)

    @mute_logger("odoo.http")
    def test_payment_route_rejects_tampered_data(self):
        """A request with an invalid access token does not reach PagBank."""
        tx = self._create_transaction(flow="direct")
        url = self._build_url("/payment/pagseguro/payment")
        with self._patch_request(self._order_response()) as request_mock:
            response = self._make_json_rpc_request(
                url,
                data={
                    "reference": tx.reference,
                    "partner_id": self.partner.id,
                    "access_token": "tampered-access-token",
                    "encrypted_card": self.encrypted_card,
                },
            )

        self.assertIn("error", response.json())
        self.assertEqual(request_mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    def test_public_key_route(self):
        """The public key of the merchant is fetched from PagBank."""
        url = self._build_url("/payment/pagseguro/public_key")
        with self._patch_request({"public_key": "PUB-KEY"}) as request_mock:
            response = self._make_json_rpc_request(
                url, data={"provider_id": self.pagseguro.id}
            )

        self.assertEqual(request_mock.call_args.args[0], "/public-keys")
        self.assertEqual(response.json()["result"], "PUB-KEY")
