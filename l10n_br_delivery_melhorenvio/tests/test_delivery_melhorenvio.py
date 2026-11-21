# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

import requests

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

ACCOUNT_MODEL = "odoo.addons.l10n_br_delivery_melhorenvio.models.melhorenvio_account"
REQUEST = ACCOUNT_MODEL + ".requests.request"
POST = ACCOUNT_MODEL + ".requests.post"
ORDER_ID = "a3384a21-3252-433d-af0b-8761c182f59d"

SERVICES = [
    {"id": 1, "name": "PAC", "company": {"id": 1, "name": "Correios"}},
    {"id": 2, "name": "SEDEX", "company": {"id": 1, "name": "Correios"}},
    {"id": 3, "name": ".Package", "company": {"id": 2, "name": "Jadlog"}},
]

QUOTE = [
    {
        "id": 1,
        "name": "PAC",
        "price": "21.50",
        "custom_price": "18.40",
        "delivery_time": 6,
        "custom_delivery_time": 5,
    },
    {"id": 2, "name": "SEDEX", "error": "Transportadora não atende este trecho."},
]


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def endpoint(call):
    return call.args[1].rsplit("/", 1)[-1]


class TestDeliveryMelhorEnvio(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env["melhorenvio.account"].create(
            {
                "name": "Loja",
                "token": "A-TOKEN",
                "client_id": "TEST-APP",
                "client_secret": "S3CRET",
                "contact_email": "suporte@example.com",
            }
        )
        with patch(REQUEST, return_value=FakeResponse(SERVICES)) as request:
            cls.account.action_sync_services()
        cls.sync_headers = request.call_args.kwargs["headers"]
        services = cls.account.carrier_ids
        cls.pac, cls.sedex, cls.package = (
            services.filtered(lambda c, s=service: c.melhorenvio_service_id == s)
            for service in (1, 2, 3)
        )
        brazil = cls.env.ref("base.br")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Cliente",
                "zip": "83824-505",
                "vat": "129.527.629-10",
                "street_name": "Avenida Rio Branco",
                "street_number": "100",
                "city": "Rio de Janeiro",
                "state_id": cls.env.ref("base.state_br_rj").id,
                "country_id": brazil.id,
                "phone": "(21) 99999-0000",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Kit", "type": "consu", "weight": 0.436, "list_price": 914.40}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )
        cls.order.warehouse_id.partner_id.write(
            {
                "zip": "01130-010",
                "vat": "86.643.372/0001-51",
                "street_name": "Avenida Paulista",
                "street_number": "1",
                "city": "São Paulo",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "country_id": brazil.id,
            }
        )

    def test_sync_services(self):
        self.assertNotIn("Authorization", self.sync_headers)
        self.assertEqual(len(self.account.carrier_ids), 3)
        self.assertEqual(self.pac.name, "Correios PAC")
        self.assertEqual(self.pac.integration_level, "rate")
        with patch(REQUEST, return_value=FakeResponse(SERVICES)):
            self.account.action_sync_services()
        self.assertEqual(len(self.account.carrier_ids), 3)

    def test_rate_shipment(self):
        with patch(REQUEST, return_value=FakeResponse(QUOTE)) as request:
            rate = self.pac.melhorenvio_rate_shipment(self.order)
        self.assertTrue(rate["success"])
        self.assertEqual(rate["price"], 18.40)
        self.assertIn("5", rate["warning_message"])
        url, kwargs = request.call_args.args[1], request.call_args.kwargs
        self.assertTrue(url.startswith("https://sandbox.melhorenvio.com.br"))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer A-TOKEN")
        self.assertEqual(kwargs["headers"]["User-Agent"], "Odoo (suporte@example.com)")
        payload = kwargs["json"]
        self.assertEqual(payload["from"]["postal_code"], "01130010")
        self.assertEqual(payload["to"]["postal_code"], "83824505")
        self.assertEqual(payload["products"][0]["weight"], self.product.weight)
        self.assertEqual(payload["services"], "1")

    def test_rate_shipment_errors(self):
        cases = [
            (self.sedex, FakeResponse(QUOTE), "trecho"),
            (self.pac, FakeResponse({}, 401), "401"),
            (self.pac, FakeResponse({"message": "Invalid data."}, 422), "Invalid"),
        ]
        for carrier, answer, message in cases:
            with patch(REQUEST, return_value=answer):
                rate = carrier.melhorenvio_rate_shipment(self.order)
            self.assertFalse(rate["success"])
            self.assertIn(message, rate["error_message"])
        unsynchronized = self.pac.copy({"melhorenvio_service_id": 0})
        rate = unsynchronized.melhorenvio_rate_shipment(self.order)
        self.assertIn("Synchronize", rate["error_message"])
        self.partner.zip = False
        rate = self.pac.melhorenvio_rate_shipment(self.order)
        self.assertIn("ZIP", rate["error_message"])

    @mute_logger(ACCOUNT_MODEL)
    def test_request_errors(self):
        with patch(REQUEST, side_effect=requests.RequestException("down")):
            with self.assertRaisesRegex(UserError, "could not be reached"):
                self.account._request("GET", "/api/v2/me/shipment/services")
        self.account.token = False
        with self.assertRaisesRegex(UserError, "Authorize"):
            self.account._request("POST", "/api/v2/me/shipment/calculate")

    def _picking(self):
        self.order.carrier_id = self.package
        self.order.action_confirm()
        return self.order.picking_ids

    def _label_answers(self, tracking=None):
        return [
            FakeResponse({"id": ORDER_ID, "protocol": "ORD-1", "status": "pending"}),
            FakeResponse(
                {
                    "purchase": {
                        "total": 18.98,
                        "orders": [
                            {"id": ORDER_ID, "price": 18.98, "status": "released"}
                        ],
                    }
                }
            ),
            FakeResponse({ORDER_ID: {"status": True}}),
            FakeResponse({"url": "https://sandbox.melhorenvio.com.br/imprimir/X"}),
            FakeResponse({ORDER_ID: {"status": "released", "tracking": tracking}}),
            # no code at the tracking endpoint yet: the order is read
            FakeResponse({"id": ORDER_ID, "self_tracking": None}),
        ]

    def test_buy_label(self):
        picking = self._picking()
        with patch(REQUEST, side_effect=self._label_answers()) as request:
            picking.action_melhorenvio_buy_label()
        self.assertEqual(picking.melhorenvio_order_id, ORDER_ID)
        self.assertEqual(picking.melhorenvio_protocol, "ORD-1")
        self.assertEqual(picking.melhorenvio_status, "released")
        self.assertEqual(picking.carrier_price, 18.98)
        self.assertEqual(picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(
            picking.action_melhorenvio_print_label()["url"],
            "https://sandbox.melhorenvio.com.br/imprimir/X",
        )
        self.assertEqual(
            [endpoint(call) for call in request.call_args_list],
            ["cart", "checkout", "generate", "print", "tracking", ORDER_ID],
        )
        cart = request.call_args_list[0].kwargs["json"]
        self.assertEqual(cart["service"], 3)
        self.assertEqual(cart["from"]["company_document"], "86643372000151")
        self.assertEqual(cart["from"]["address"], "Avenida Paulista")
        self.assertEqual(cart["to"]["document"], "12952762910")
        self.assertEqual(cart["to"]["number"], "100")
        self.assertEqual(cart["to"]["phone"], "21999990000")
        self.assertEqual(cart["products"][0]["quantity"], "1")
        self.assertTrue(cart["options"]["non_commercial"])
        self.assertEqual(cart["options"]["tags"][0]["tag"], picking.name)

    def test_buy_label_with_invoice_key(self):
        picking = self._picking()
        key = "35261186643372000151550010000000011000000010"
        with patch.object(
            type(self.package), "_melhorenvio_invoice_key", return_value=key
        ):
            cart = self.package._melhorenvio_cart_payload(picking)
        self.assertFalse(cart["options"]["non_commercial"])
        self.assertEqual(cart["options"]["invoice"], {"key": key})

    def test_buy_label_resumes_without_paying_twice(self):
        picking = self._picking()
        answers = self._label_answers()
        refused = FakeResponse({"message": "Saldo insuficiente"}, 422)
        with patch(REQUEST, side_effect=[answers[0], refused]):
            picking.action_melhorenvio_buy_label()
        self.assertEqual(picking.melhorenvio_order_id, ORDER_ID)
        self.assertEqual(picking.melhorenvio_status, "pending")
        self.assertIn("Saldo insuficiente", picking.message_ids[0].body)
        # The retry reads the order and pays the same cart entry.
        pending = FakeResponse({"id": ORDER_ID, "status": "pending"})
        with patch(REQUEST, side_effect=[pending, *answers[1:]]) as request:
            picking.action_melhorenvio_buy_label()
        self.assertEqual(
            [endpoint(call) for call in request.call_args_list][:3],
            [ORDER_ID, "checkout", "generate"],
        )
        # Paid at Melhor Envio but not stored here: no second checkout.
        picking.write({"melhorenvio_status": "pending", "melhorenvio_label_url": False})
        released = FakeResponse({"id": ORDER_ID, "status": "released", "price": 18.98})
        with patch(REQUEST, side_effect=[released, *answers[2:]]) as request:
            picking.action_melhorenvio_buy_label()
        self.assertNotIn("checkout", [endpoint(c) for c in request.call_args_list])
        self.assertEqual(picking.carrier_price, 18.98)
        self.assertTrue(picking.melhorenvio_label_url)

    def test_buy_label_missing_document(self):
        picking = self._picking()
        self.partner.vat = False
        with self.assertRaisesRegex(UserError, "CPF"):
            picking.action_melhorenvio_buy_label()

    def test_tracking_update_and_cancel(self):
        picking = self._picking()
        with patch(REQUEST, side_effect=self._label_answers(tracking="JD9")):
            result = self.package.melhorenvio_send_shipping(picking)
        self.assertEqual(result, [{"exact_price": 18.98, "tracking_number": "JD9"}])
        picking.carrier_tracking_ref = "JD9"
        posted = FakeResponse({ORDER_ID: {"status": "posted", "tracking": "JD123BR"}})
        with patch(REQUEST, return_value=posted):
            picking.tracking_state_update()
        self.assertEqual(picking.carrier_tracking_ref, "JD123BR")
        self.assertEqual(picking.delivery_state, "in_transit")
        self.assertIn("JD123BR", self.package.melhorenvio_get_tracking_link(picking))
        answers = [
            FakeResponse({ORDER_ID: {"status": "delivered", "tracking": None}}),
            FakeResponse({"id": ORDER_ID, "self_tracking": "ME26006NLF4BR"}),
        ]
        with patch(REQUEST, side_effect=answers):
            picking.tracking_state_update()
        self.assertEqual(picking.delivery_state, "customer_delivered")
        self.assertEqual(picking.carrier_tracking_ref, "ME26006NLF4BR")
        with patch(REQUEST, return_value=FakeResponse({})) as request:
            self.package.melhorenvio_cancel_shipment(picking)
        self.assertEqual(request.call_args.kwargs["json"]["order"]["id"], ORDER_ID)
        self.assertEqual(picking.delivery_state, "canceled_shipment")

    def test_oauth_authorize_and_exchange(self):
        self.account.write(
            {"redirect_uri": "https://odoo.example.com/cb", "token": False}
        )
        action = self.account.action_authorize()
        self.assertIn("sandbox.melhorenvio.com.br/oauth/authorize", action["url"])
        self.assertIn("client_id=TEST-APP", action["url"])
        self.assertIn(self.account.oauth_state, action["url"])
        answer = FakeResponse(
            {"access_token": "NEW", "refresh_token": "REF", "expires_in": 2592000}
        )
        with patch(POST, return_value=answer) as post:
            self.account._exchange_token(
                {"grant_type": "authorization_code", "code": "C0DE"}
            )
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["code"], "C0DE")
        self.assertEqual(payload["client_secret"], "S3CRET")
        self.assertEqual(payload["redirect_uri"], "https://odoo.example.com/cb")
        self.assertEqual(self.account.token, "NEW")
        self.assertFalse(self.account.oauth_state)
        self.assertTrue(self.account.token_expiry)

    def test_oauth_refresh_and_refusal(self):
        self.account.write(
            {"refresh_token": "REF", "token_expiry": "2020-01-01 00:00:00"}
        )
        answer = FakeResponse(
            {"access_token": "FRESH", "refresh_token": "REF2", "expires_in": 2592000}
        )
        with patch(POST, return_value=answer) as post:
            headers = self.account._headers()
        self.assertEqual(post.call_args.kwargs["json"]["grant_type"], "refresh_token")
        self.assertEqual(headers["Authorization"], "Bearer FRESH")
        refused = FakeResponse({"error": "invalid_grant", "message": "Bad code"}, 400)
        with patch(POST, return_value=refused):
            with self.assertRaisesRegex(UserError, "Bad code"):
                self.account._exchange_token(
                    {"grant_type": "authorization_code", "code": "X"}
                )


@tagged("post_install", "-at_install")
class TestMelhorEnvioOAuthCallback(HttpCase):
    def test_callback_stores_the_token(self):
        account = self.env["melhorenvio.account"].create(
            {
                "name": "Loja",
                "client_id": "TEST-APP",
                "client_secret": "S3CRET",
                "contact_email": "suporte@example.com",
                "oauth_state": "STATE",
            }
        )
        self.authenticate("admin", "admin")
        answer = FakeResponse({"access_token": "NEW", "expires_in": 2592000})
        with patch(POST, return_value=answer):
            response = self.url_open(
                "/melhorenvio/oauth/callback?code=C0DE&state=STATE",
                allow_redirects=False,
            )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(account.token, "NEW")
