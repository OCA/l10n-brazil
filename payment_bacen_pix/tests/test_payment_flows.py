# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from .common import BacenPixCommon

_PIX_LOGGER = "odoo.addons.payment_bacen_pix.models.payment_transaction"


@tagged("post_install", "-at_install")
class TestBacenPixCharge(BacenPixCommon):
    def test_charge_payload(self):
        """The charge sent to the PSP follows the payload of the Pix API."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_create_charge()

        endpoint, payload = request_mock.call_args.args
        self.assertTrue(endpoint.startswith("/cob/"))
        self.assertEqual(request_mock.call_args.kwargs["method"], "PUT")
        self.assertEqual(payload["calendario"]["expiracao"], 3600)
        self.assertEqual(payload["valor"]["original"], "1111.11")
        self.assertEqual(payload["chave"], "pix-key@example.com")
        self.assertEqual(payload["solicitacaoPagador"], self.reference)

    def test_txid_follows_the_pix_pattern(self):
        """The txid is alphanumeric and 26 to 35 characters long."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_create_charge()

        txid = request_mock.call_args.args[0].split("/")[-1]
        self.assertTrue(txid.isalnum())
        self.assertTrue(26 <= len(txid) <= 35)

    def test_debtor_is_sent_with_a_cpf(self):
        """A partner with a CPF is sent as the debtor of the charge."""
        self.partner.vat = "191.867.470-58"
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_create_charge()

        self.assertEqual(
            request_mock.call_args.args[1]["devedor"],
            {"cpf": "19186747058", "nome": self.partner.name},
        )

    def test_debtor_is_sent_with_a_cnpj(self):
        """A partner with a CNPJ is sent as the debtor of the charge."""
        self.partner.vat = "11.222.333/0001-81"
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_create_charge()

        self.assertEqual(
            request_mock.call_args.args[1]["devedor"]["cnpj"], "11222333000181"
        )

    def test_debtor_is_left_out_without_a_tax_id(self):
        """The Pix API refuses a debtor without a valid CPF or CNPJ."""
        self.partner.vat = False
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_create_charge()

        self.assertNotIn("devedor", request_mock.call_args.args[1])

    def test_charge_stores_the_qr_code(self):
        """The payload of the QR code is saved to be shown to the payer."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        self.assertEqual(tx.bacenpix_txid, self.txid)
        self.assertEqual(tx.bacenpix_qrcode, self.qr_code)
        self.assertEqual(tx.bacenpix_location, f"pix.example.com/qr/v2/{self.txid}")
        self.assertEqual(tx.state, "pending")

    def test_expiration_is_computed_from_the_calendar(self):
        """The moment the charge expires comes from its creation plus its ttl."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        self.assertEqual(str(tx.bacenpix_expiration), "2026-07-27 21:00:00")

    def test_charge_without_qr_code_is_rejected(self):
        """A charge that comes back without a payload is an error."""
        tx = self._create_transaction(flow="redirect")
        response = self._charge_response()
        response.pop("pixCopiaECola")
        with self._patch_request(response), self.assertRaises(ValidationError):
            tx._bacenpix_create_charge()

    def test_rendering_values_create_the_charge(self):
        """The QR code is ready when the payer reaches the payment page."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()), patch(
            "odoo.addons.payment.utils.generate_access_token",
            new=self._generate_test_access_token,
        ):
            rendering_values = tx._get_specific_rendering_values({})

        self.assertEqual(rendering_values["api_url"], "/payment/bacenpix/qrcode")
        self.assertEqual(rendering_values["reference"], self.reference)
        self.assertTrue(rendering_values["access_token"])
        self.assertTrue(tx.bacenpix_qrcode)

    def test_charge_is_not_created_twice(self):
        """A transaction that already has a charge does not create another."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock, patch(
            "odoo.addons.payment.utils.generate_access_token",
            new=self._generate_test_access_token,
        ):
            tx._get_specific_rendering_values({})
            tx._get_specific_rendering_values({})

        self.assertEqual(request_mock.call_count, 1)


@tagged("post_install", "-at_install")
class TestBacenPixNotificationData(BacenPixCommon):
    def _process(self, status, with_payment=False, **kwargs):
        tx = self._create_transaction(flow="redirect", **kwargs)
        tx._handle_notification_data(
            "bacenpix", {"response": self._charge_response(status, with_payment)}
        )
        return tx

    def test_active_charge_sets_the_transaction_pending(self):
        tx = self._process("ATIVA")
        self.assertEqual(tx.state, "pending")

    def test_paid_charge_sets_the_transaction_done(self):
        tx = self._process("CONCLUIDA", with_payment=True)
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, self.end_to_end_id)

    def test_removed_charge_cancels_the_transaction(self):
        for status in ("REMOVIDA_PELO_USUARIO_RECEBEDOR", "REMOVIDA_PELO_PSP"):
            self.reference = f"Test Transaction {status}"
            tx = self._process(status)
            self.assertEqual(tx.state, "cancel")

    @mute_logger(_PIX_LOGGER)
    def test_unknown_status_sets_the_transaction_in_error(self):
        tx = self._process("SOMETHING_ELSE")
        self.assertEqual(tx.state, "error")

    def test_missing_status_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self.assertRaises(ValidationError):
            tx._handle_notification_data("bacenpix", {"response": {"txid": self.txid}})

    def test_transaction_is_found_from_the_txid(self):
        """The txid sent back by the PSP identifies the transaction."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        found_tx = self.env["payment.transaction"]._get_tx_from_notification_data(
            "bacenpix", {"response": self._charge_response()}
        )
        self.assertEqual(found_tx, tx)

    def test_unknown_txid_is_rejected(self):
        self._create_transaction(flow="redirect")
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._get_tx_from_notification_data(
                "bacenpix", {"response": {"txid": "no-such-txid"}}
            )


@tagged("post_install", "-at_install")
class TestBacenPixPolling(BacenPixCommon):
    def test_polling_processes_the_payment(self):
        """Querying the charge is what confirms the payment without a webhook."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        with self._patch_request(
            self._charge_response("CONCLUIDA", with_payment=True)
        ) as request_mock:
            tx._bacenpix_poll_charge()

        self.assertEqual(request_mock.call_args.args[0], f"/cob/{self.txid}")
        self.assertEqual(request_mock.call_args.kwargs["method"], "GET")
        self.assertEqual(tx.state, "done")

    def test_polling_ignores_transactions_without_a_charge(self):
        """A transaction that never reached the PSP is not queried."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()) as request_mock:
            tx._bacenpix_poll_charge()

        self.assertEqual(request_mock.call_count, 0)

    def test_cron_polls_the_pending_transactions(self):
        """The cron queries the charges that are still waiting for a payment."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        with self._patch_request(
            self._charge_response("CONCLUIDA", with_payment=True)
        ) as request_mock:
            self.env["payment.transaction"]._cron_bacenpix_poll_pending_transactions()

        self.assertTrue(request_mock.call_count)
        self.assertEqual(tx.state, "done")

    @mute_logger(_PIX_LOGGER)
    def test_cron_survives_a_failing_psp(self):
        """One charge that cannot be queried does not stop the cron."""
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()

        with patch(
            "odoo.addons.payment_bacen_pix.models.payment_provider.PaymentProvider"
            "._bacenpix_make_request",
            side_effect=ValidationError("Pix: down"),
        ):
            self.env["payment.transaction"]._cron_bacenpix_poll_pending_transactions()

        self.assertEqual(tx.state, "pending")


@tagged("post_install", "-at_install")
class TestBacenPixController(BacenPixCommon, PaymentHttpCommon):
    def _create_charged_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._patch_request(self._charge_response()):
            tx._bacenpix_create_charge()
        return tx

    def test_qrcode_page_shows_the_payload(self):
        """The page of the QR code carries the copy and paste payload."""
        tx = self._create_charged_transaction()
        url = self._build_url("/payment/bacenpix/qrcode")
        response = self._make_http_post_request(
            url,
            data={
                "reference": tx.reference,
                "access_token": self._generate_test_access_token(
                    tx.reference, self.partner.id
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.qr_code, response.text)

    @mute_logger("odoo.http")
    def test_qrcode_page_rejects_tampered_data(self):
        """The page cannot be opened with an invalid access token."""
        tx = self._create_charged_transaction()
        url = self._build_url("/payment/bacenpix/qrcode")
        response = self._make_http_post_request(
            url,
            data={"reference": tx.reference, "access_token": "tampered-access-token"},
        )

        self.assertNotIn(self.qr_code, response.text)

    def test_status_route_polls_the_charge(self):
        """The page polls the state of the transaction while it is pending."""
        tx = self._create_charged_transaction()
        url = self._build_url("/payment/bacenpix/status")
        with self._patch_request(self._charge_response("CONCLUIDA", with_payment=True)):
            response = self._make_json_rpc_request(
                url,
                data={
                    "reference": tx.reference,
                    "access_token": self._generate_test_access_token(
                        tx.reference, self.partner.id
                    ),
                },
            )

        self.assertEqual(response.json()["result"]["state"], "done")
        self.assertEqual(tx.state, "done")

    def test_webhook_confirms_the_payment(self):
        """The notification of the PSP triggers a query of the charge."""
        tx = self._create_charged_transaction()
        url = self._build_url("/payment/bacenpix/webhook")
        with self._patch_request(self._charge_response("CONCLUIDA", with_payment=True)):
            self._make_json_request(
                url,
                data={
                    "pix": [
                        {
                            "endToEndId": self.end_to_end_id,
                            "txid": self.txid,
                            "valor": "1111.11",
                        }
                    ]
                },
            )

        self.assertEqual(tx.state, "done")

    @mute_logger("odoo.addons.payment_bacen_pix.controllers.main")
    def test_webhook_ignores_unknown_txid(self):
        """A notification for another merchant does not raise."""
        url = self._build_url("/payment/bacenpix/webhook")
        with self._patch_request(self._charge_response()) as request_mock:
            response = self._make_json_request(
                url, data={"pix": [{"txid": "no-such-txid"}]}
            )

        self.assertNotIn("error", response.json())
        self.assertEqual(request_mock.call_count, 0)
