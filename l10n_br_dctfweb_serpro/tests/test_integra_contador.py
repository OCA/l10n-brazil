# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
from contextlib import contextmanager
from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models import integra_contador
from .common import MOCK_POST, TestSerproCommon, answer

CERTIFICATE_PATH = (
    "odoo.addons.l10n_br_dctfweb_serpro.models.integra_contador."
    "IntegraContador._certificate_files"
)


@contextmanager
def fake_certificate(*args, **kwargs):
    yield ("/tmp/cert.pem", "/tmp/key.pem")


@tagged("post_install", "-at_install")
class TestIntegraContador(TestSerproCommon):
    """The transport: envelope, errors and what never reaches the log."""

    def setUp(self):
        super().setUp()
        self.transport = self.env["l10n_br_dctfweb.integra.contador"]
        patcher = mock.patch(CERTIFICATE_PATH, side_effect=fake_certificate)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_the_envelope_carries_the_three_parties_and_the_service(self):
        request = self.transport._build_request(
            self.company, "12345678000195", "close_assessment", {"a": 1}
        )
        self.assertEqual(request["contribuinte"]["numero"], "12345678000195")
        self.assertEqual(request["contratante"]["numero"], "12345678000195")
        self.assertEqual(request["autorPedidoDados"]["numero"], "12345678000195")
        self.assertEqual(request["pedidoDados"]["idSistema"], "MIT")
        self.assertEqual(request["pedidoDados"]["idServico"], "ENCAPURACAO314")
        self.assertEqual(request["pedidoDados"]["versaoSistema"], "1.0")

    def test_the_data_is_a_json_string_not_an_object(self):
        """The platform takes "dados" as a string, and refuses an object."""
        request = self.transport._build_request(
            self.company, "12345678000195", "close_assessment", {"a": 1}
        )
        data = request["pedidoDados"]["dados"]
        self.assertIsInstance(data, str)
        self.assertEqual(json.loads(data), {"a": 1})

    def test_the_contractor_can_be_the_accounting_firm(self):
        self.company.sudo().serpro_contractor_cnpj = "98765432000199"
        request = self.transport._build_request(
            self.company, "12345678000195", "close_assessment", {}
        )
        self.assertEqual(request["contratante"]["numero"], "98765432000199")
        self.assertEqual(request["contribuinte"]["numero"], "12345678000195")

    def test_a_nested_data_string_comes_back_parsed(self):
        with mock.patch(MOCK_POST, return_value=answer({"idApuracao": 7})):
            body = self.transport.call(
                self.company, "12345678000195", "close_assessment", {}
            )
        self.assertEqual(body["dados"], {"idApuracao": 7})
        self.assertTrue(self.transport.succeeded(body))

    def test_a_timeout_becomes_a_user_error(self):
        with mock.patch(
            MOCK_POST, side_effect=requests.exceptions.Timeout
        ), self.assertRaises(UserError):
            self.transport.call(self.company, "12345678000195", "close_assessment", {})

    def test_a_connection_error_becomes_a_user_error(self):
        with mock.patch(
            MOCK_POST, side_effect=requests.exceptions.ConnectionError
        ), self.assertRaises(UserError):
            self.transport.call(self.company, "12345678000195", "close_assessment", {})

    def test_an_http_error_without_a_body_becomes_a_user_error(self):
        with mock.patch(MOCK_POST, return_value=answer(None, http_status=500)) as post:
            post.return_value.payload = {}
            with self.assertRaises(UserError):
                self.transport.call(
                    self.company, "12345678000195", "close_assessment", {}
                )

    def test_the_authority_messages_are_readable(self):
        body = {
            "mensagens": [
                {"codigo": "[Erro-MIT]", "texto": "Apuracao ja encerrada."},
                {"codigo": "[Aviso]", "texto": "Confira o periodo."},
            ]
        }
        self.assertEqual(
            self.transport.messages(body),
            "[Erro-MIT] Apuracao ja encerrada.\n[Aviso] Confira o periodo.",
        )

    def test_production_without_credentials_is_refused(self):
        self.company.sudo().write(
            {
                "serpro_environment": "production",
                "serpro_consumer_key": False,
                "serpro_consumer_secret": False,
            }
        )
        with self.assertRaises(UserError):
            self.transport._get_token(self.company)

    def test_the_token_is_asked_with_basic_auth_and_the_certificate(self):
        self.company.sudo().write(
            {
                "serpro_environment": "production",
                "serpro_access_token": False,
                "serpro_token_expiration": False,
            }
        )
        response = answer({})
        response.payload = {"access_token": "fresh", "expires_in": 3600}
        with mock.patch(MOCK_POST, return_value=response) as post:
            token = self.transport._get_token(self.company)
        self.assertEqual(token, "fresh")
        headers = post.call_args.kwargs["headers"]
        self.assertTrue(headers["Authorization"].startswith("Basic "))
        self.assertEqual(
            post.call_args.kwargs["cert"], ("/tmp/cert.pem", "/tmp/key.pem")
        )
        self.assertTrue(post.call_args.kwargs["timeout"])
        self.assertTrue(self.company.sudo().serpro_token_expiration)

    def test_a_stored_token_is_reused(self):
        self.company.sudo().write(
            {
                "serpro_environment": "production",
                "serpro_access_token": "still-good",
                "serpro_token_expiration": "2099-01-01 00:00:00",
            }
        )
        with mock.patch(MOCK_POST) as post:
            token = self.transport._get_token(self.company)
        self.assertEqual(token, "still-good")
        post.assert_not_called()

    def test_every_request_has_a_timeout(self):
        """A call without a timeout can hang a worker forever."""
        with mock.patch(MOCK_POST, return_value=answer({})) as post:
            self.transport.call(self.company, "12345678000195", "close_assessment", {})
        self.assertTrue(post.call_args.kwargs["timeout"])

    def test_the_token_never_reaches_the_log(self):
        """The log gets the service and the record, never the credential."""
        with mock.patch.object(integra_contador._logger, "info") as info, mock.patch(
            MOCK_POST, return_value=answer({})
        ):
            self.transport.call(
                self.company,
                "12345678000195",
                "close_assessment",
                {"secret": "value"},
                record=self.mit,
            )
        info.assert_called_once()
        written = " ".join(str(argument) for argument in info.call_args.args)
        self.assertIn("ENCAPURACAO314", written)
        self.assertNotIn("a-token", written)
        self.assertNotIn("secret", written)
        self.assertNotIn("12345678000195", written)
