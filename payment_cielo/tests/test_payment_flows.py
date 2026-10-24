# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from .common import CieloCommon

_TX_LOGGER = "odoo.addons.payment.models.payment_transaction"
_CIELO_LOGGER = "odoo.addons.payment_cielo.models.payment_transaction"


@tagged("post_install", "-at_install")
class TestCieloPaymentFlows(CieloCommon):
    def test_direct_payment_sends_the_card_to_cielo(self):
        """The card details are forwarded to Cielo, never saved in the database."""
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._sale_response()) as request_mock:
            tx._cielo_create_sale(card_data=self.card_data)

        endpoint, payload = request_mock.call_args.args
        self.assertEqual(endpoint, "/1/sales")
        self.assertEqual(payload["MerchantOrderId"], self.reference)
        self.assertEqual(payload["Customer"]["Name"], self.partner.name)
        self.assertEqual(payload["Payment"]["Amount"], 111111)
        self.assertEqual(payload["Payment"]["Type"], "CreditCard")
        self.assertTrue(payload["Payment"]["Capture"])
        card_payload = payload["Payment"]["CreditCard"]
        self.assertEqual(card_payload["CardNumber"], "4024007197692931")
        self.assertEqual(card_payload["ExpirationDate"], "02/2030")
        self.assertEqual(card_payload["SecurityCode"], "123")
        self.assertEqual(card_payload["Brand"], "Visa")
        self.assertFalse(card_payload["SaveCard"])

    def test_soft_descriptor_is_truncated(self):
        """Cielo rejects soft descriptors longer than 13 characters."""
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._sale_response()) as request_mock:
            tx._cielo_create_sale(card_data=self.card_data)

        soft_descriptor = request_mock.call_args.args[1]["Payment"]["SoftDescriptor"]
        self.assertEqual(soft_descriptor, "Odoo Communit")

    def test_manual_capture_only_authorizes_the_payment(self):
        """The payment is not captured along with the sale when capturing manually."""
        self.cielo.capture_manually = True
        tx = self._create_transaction(flow="direct")
        with self._patch_request(self._sale_response(status=1)) as request_mock:
            tx._cielo_create_sale(card_data=self.card_data)

        self.assertFalse(request_mock.call_args.args[1]["Payment"]["Capture"])

    def test_validation_only_authorizes_the_payment(self):
        """Validation transactions are voided right after being authorized."""
        tx = self._create_transaction(flow="direct", operation="validation")
        with self._patch_request(self._sale_response(status=1)) as request_mock:
            tx._cielo_create_sale(card_data=self.card_data)

        self.assertFalse(request_mock.call_args.args[1]["Payment"]["Capture"])

    def test_unsupported_card_brand_is_rejected(self):
        """A card whose brand cannot be detected is rejected before any request."""
        tx = self._create_transaction(flow="direct")
        card_data = dict(self.card_data, card_number="9999999999999999")
        with self._patch_request(self._sale_response()) as request_mock:
            with self.assertRaises(ValidationError):
                tx._cielo_create_sale(card_data=card_data)
        self.assertEqual(request_mock.call_count, 0)

    def test_payment_by_token_uses_the_card_token(self):
        """A payment made with a token sends the card token and its brand."""
        token = self._create_token(
            provider_ref=self.card_token, cielo_card_brand="Visa"
        )
        tx = self._create_transaction(flow="token", token_id=token.id)
        with self._patch_request(self._sale_response()) as request_mock, mute_logger(
            _TX_LOGGER
        ):
            tx._send_payment_request()

        card_payload = request_mock.call_args.args[1]["Payment"]["CreditCard"]
        self.assertEqual(card_payload["CardToken"], self.card_token)
        self.assertEqual(card_payload["Brand"], "Visa")
        self.assertEqual(tx.state, "done")

    def test_payment_without_card_nor_token_is_rejected(self):
        """A payment with neither card details nor token never reaches Cielo."""
        tx = self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            tx._cielo_prepare_card_payload()

    def test_tokenization_saves_the_card_token(self):
        """Cielo returns a card token that is saved when the customer asked for it."""
        tx = self._create_transaction(flow="direct", tokenize=True)
        with self._patch_request(self._sale_response()) as request_mock:
            tx._cielo_create_sale(card_data=self.card_data)
        self.assertTrue(
            request_mock.call_args.args[1]["Payment"]["CreditCard"]["SaveCard"]
        )

        tx._handle_notification_data(
            "cielo", {"response": self._sale_response(save_card=True)}
        )

        self.assertEqual(tx.state, "done")
        self.assertTrue(tx.token_id)
        self.assertEqual(tx.token_id.provider_ref, self.card_token)
        self.assertEqual(tx.token_id.payment_details, "2931")
        self.assertEqual(tx.token_id.cielo_card_brand, "Visa")
        self.assertTrue(tx.token_id.verified)
        self.assertFalse(tx.tokenize, "the tokenization must not be requested twice")

    @mute_logger(_CIELO_LOGGER)
    def test_no_token_is_created_without_a_card_token(self):
        """No token is created when Cielo does not return the card token."""
        tx = self._create_transaction(flow="direct", tokenize=True)
        tx._handle_notification_data("cielo", {"response": self._sale_response()})

        self.assertEqual(tx.state, "done")
        self.assertFalse(tx.token_id)

    def test_transaction_is_found_from_the_merchant_order_id(self):
        """The reference sent back by Cielo identifies the transaction."""
        tx = self._create_transaction(flow="direct")
        found_tx = self.env["payment.transaction"]._get_tx_from_notification_data(
            "cielo", {"response": self._sale_response()}
        )
        self.assertEqual(found_tx, tx)

    def test_unknown_reference_is_rejected(self):
        """A notification that matches no transaction is rejected."""
        self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._get_tx_from_notification_data(
                "cielo", {"reference": "no-such-reference"}
            )


@tagged("post_install", "-at_install")
class TestCieloNotificationData(CieloCommon):
    def _process(self, status, **kwargs):
        tx = self._create_transaction(flow="direct", **kwargs)
        tx._handle_notification_data("cielo", {"response": self._sale_response(status)})
        return tx

    def test_paid_payment_sets_the_transaction_done(self):
        tx = self._process(2)
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, self.payment_id)

    def test_authorized_payment_sets_the_transaction_authorized(self):
        self.cielo.capture_manually = True
        tx = self._process(1)
        self.assertEqual(tx.state, "authorized")

    @mute_logger(_CIELO_LOGGER)
    def test_authorized_payment_without_capture_is_an_error(self):
        """A sale requested with capture must not stay authorized silently."""
        tx = self._process(1)
        self.assertEqual(tx.state, "error")

    def test_not_finished_payment_sets_the_transaction_pending(self):
        for status in (0, 12, 20):
            self.reference = f"Test Transaction {status}"
            tx = self._process(status)
            self.assertEqual(tx.state, "pending")

    @mute_logger(_CIELO_LOGGER)
    def test_denied_payment_sets_the_transaction_in_error(self):
        for status in (3, 13):
            self.reference = f"Test Transaction {status}"
            tx = self._process(status)
            self.assertEqual(tx.state, "error")
            self.assertIn("Operation Successful", tx.state_message)

    def test_voided_payment_cancels_the_transaction(self):
        tx = self._process(10)
        self.assertEqual(tx.state, "cancel")

    @mute_logger(_CIELO_LOGGER)
    def test_unknown_status_sets_the_transaction_in_error(self):
        tx = self._process(999)
        self.assertEqual(tx.state, "error")

    def test_missing_status_is_rejected(self):
        tx = self._create_transaction(flow="direct")
        with self.assertRaises(ValidationError):
            tx._handle_notification_data("cielo", {"response": {"Payment": {}}})


@tagged("post_install", "-at_install")
class TestCieloOperations(CieloCommon):
    def setUp(self):
        super().setUp()
        self.cielo.capture_manually = True

    def test_capture_request(self):
        """The authorized payment is captured for the amount of the transaction."""
        tx = self._create_transaction(
            flow="direct", state="authorized", provider_reference=self.payment_id
        )
        with self._patch_request(self._operation_response(status=2)) as request_mock:
            tx._send_capture_request()

        endpoint = request_mock.call_args.args[0]
        self.assertEqual(endpoint, f"/1/sales/{self.payment_id}/capture?amount=111111")
        self.assertEqual(request_mock.call_args.kwargs["method"], "PUT")
        self.assertEqual(tx.state, "done")

    def test_void_request(self):
        """The authorized payment is voided in full."""
        tx = self._create_transaction(
            flow="direct", state="authorized", provider_reference=self.payment_id
        )
        with self._patch_request(self._operation_response(status=10)) as request_mock:
            tx._send_void_request()

        self.assertEqual(
            request_mock.call_args.args[0], f"/1/sales/{self.payment_id}/void"
        )
        self.assertEqual(tx.state, "cancel")

    @mute_logger(_TX_LOGGER)
    def test_refund_request(self):
        """A captured payment is refunded through the void endpoint."""
        tx = self._create_transaction(
            flow="direct", state="done", provider_reference=self.payment_id
        )
        with self._patch_request(self._operation_response(status=11)) as request_mock:
            refund_tx = tx._send_refund_request()

        self.assertEqual(
            request_mock.call_args.args[0],
            f"/1/sales/{self.payment_id}/void?amount=111111",
        )
        self.assertTrue(refund_tx)
        self.assertEqual(refund_tx.operation, "refund")
        self.assertEqual(refund_tx.source_transaction_id, tx)
        self.assertEqual(refund_tx.amount, -self.amount)
        self.assertEqual(refund_tx.state, "done")

    def test_validation_is_authorized_then_voided(self):
        """Saving a card authorizes a small amount and voids it right away."""
        tx = self._create_transaction(flow="direct", operation="validation")
        with self._patch_request(self._operation_response(status=10)):
            tx._handle_notification_data(
                "cielo", {"response": self._sale_response(status=1)}
            )

        self.assertEqual(tx.state, "done")


@tagged("post_install", "-at_install")
class TestCieloController(CieloCommon, PaymentHttpCommon):
    def test_payment_route_processes_the_payment(self):
        """The payment route forwards the card details and processes the response."""
        tx = self._create_transaction(flow="direct")
        url = self._build_url("/payment/cielo/payment")
        with self._patch_request(self._sale_response()):
            self._make_json_rpc_request(
                url,
                data={
                    "reference": tx.reference,
                    "partner_id": self.partner.id,
                    "access_token": self._generate_test_access_token(
                        tx.reference, self.partner.id
                    ),
                    "card_data": self.card_data,
                },
            )

        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, self.payment_id)

    @mute_logger("odoo.http")
    def test_payment_route_rejects_tampered_data(self):
        """A request with an invalid access token does not reach Cielo."""
        tx = self._create_transaction(flow="direct")
        url = self._build_url("/payment/cielo/payment")
        with self._patch_request(self._sale_response()) as request_mock:
            response = self._make_json_rpc_request(
                url,
                data={
                    "reference": tx.reference,
                    "partner_id": self.partner.id,
                    "access_token": "tampered-access-token",
                    "card_data": self.card_data,
                },
            )

        self.assertIn("error", response.json())
        self.assertEqual(request_mock.call_count, 0)
        self.assertEqual(tx.state, "draft")
