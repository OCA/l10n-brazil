# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest.mock import patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

MODEL_LOGGER = "odoo.addons.l10n_br_delivery_frenet.models.delivery_carrier"

REQUESTS = (
    "odoo.addons.l10n_br_delivery_frenet.models.delivery_carrier.requests.request"
)

SHIPPING_INFO = {
    "ShippingSeviceAvailableArray": [
        {
            "ServiceCode": "03298",
            "ServiceDescription": "PAC",
            "Carrier": "Correios",
            "CarrierCode": "COR",
        },
        {
            "ServiceCode": "03220",
            "ServiceDescription": "Sedex",
            "Carrier": "Correios",
            "CarrierCode": "COR",
        },
        {
            "ServiceCode": "F_3",
            "ServiceDescription": "Jadlog Package",
            "Carrier": "Jadlog",
            "CarrierCode": "JAD",
        },
    ]
}

QUOTE = {
    "ShippingSevicesArray": [
        {
            "ServiceCode": "03298",
            "ServiceDescription": "PAC",
            "Carrier": "Correios",
            "ShippingPrice": "18.40",
            "DeliveryTime": "5",
            "Error": False,
        },
        {
            "ServiceCode": "04227",
            "ServiceDescription": "Mini Envios",
            "Carrier": "Correios",
            "Msg": "Erro: A soma das dimensões excede o limite para o PAC MINI",
            "Error": True,
        },
    ]
}

TRACKING = {
    "ServiceDescrition": "PAC",
    "TrackingUrl": "https://rastreio.frenet.com.br/COR/BR267566353956A",
    "TrackingEvents": [
        {
            "EventDateTime": "27/01/2026 15:20",
            "EventDescription": "Objeto postado",
            "EventLocation": "São Paulo-SP",
            "EventType": "0",
        },
        {
            "EventDateTime": "10/02/2026 16:48",
            "EventDescription": "Objeto entregue ao destinatário",
            "EventLocation": "Fazenda Rio Grande-PR",
            "EventType": "9",
        },
    ],
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class TestDeliveryFrenet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_id.zip = "01130-010"
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Frenet",
                "delivery_type": "frenet",
                "frenet_token": "A-TOKEN",
                "product_id": cls.env.ref(
                    "l10n_br_delivery_frenet.product_product_delivery_frenet"
                ).id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Kit", "type": "consu", "weight": 0.436, "list_price": 914.40}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Cliente", "zip": "83824-505"}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def _sync(self):
        with patch(REQUESTS, return_value=FakeResponse(SHIPPING_INFO)):
            self.carrier.action_frenet_sync_services()
        return self.env["delivery.carrier"].search(
            [("delivery_type", "=", "frenet"), ("frenet_service_code", "!=", False)]
        )

    def test_sync_services(self):
        carriers = self._sync()
        self.assertEqual(len(carriers), 3)
        pac = carriers.filtered(lambda c: c.frenet_service_code == "03298")
        self.assertEqual(pac.name, "Correios PAC")
        self.assertEqual(pac.frenet_carrier_code, "COR")
        self.assertEqual(pac.frenet_token, "A-TOKEN")
        # Running it again updates instead of duplicating
        self.assertEqual(len(self._sync()), 3)

    def test_rate_shipment(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        with patch(REQUESTS, return_value=FakeResponse(QUOTE)) as request:
            rate = pac.frenet_rate_shipment(self.order)
        self.assertTrue(rate["success"])
        self.assertEqual(rate["price"], 18.40)
        self.assertEqual(rate["frenet_delivery_time"], 5)
        self.assertIn("5", rate["warning_message"])
        payload = request.call_args.kwargs["json"]
        self.assertEqual(payload["SellerCEP"], "01130010")
        self.assertEqual(payload["RecipientCEP"], "83824505")
        self.assertEqual(payload["ShippingItemArray"][0]["Weight"], self.product.weight)
        self.assertEqual(payload["ShippingServiceCode"], "03298")

    def test_rate_shipment_service_error(self):
        mini = self._sync().filtered(lambda c: c.frenet_service_code == "03220")
        mini.frenet_service_code = "04227"
        with patch(REQUESTS, return_value=FakeResponse(QUOTE)):
            rate = mini.frenet_rate_shipment(self.order)
        self.assertFalse(rate["success"])
        self.assertIn("PAC MINI", rate["error_message"])

    def test_rate_shipment_missing_zip(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        self.partner.zip = False
        rate = pac.frenet_rate_shipment(self.order)
        self.assertFalse(rate["success"])

    def test_tracking(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        self.order.carrier_id = pac
        self.order.action_confirm()
        picking = self.order.picking_ids[0]
        picking.carrier_tracking_ref = "BR267566353956A"
        self.assertEqual(
            pac.frenet_get_tracking_link(picking),
            "https://rastreio.frenet.com.br/COR/BR267566353956A",
        )
        with patch(REQUESTS, return_value=FakeResponse(TRACKING)):
            pac.frenet_tracking_state_update(picking)
        self.assertEqual(picking.delivery_state, "customer_delivered")
        self.assertIn("Objeto entregue", picking.tracking_state)
        self.assertIn("Objeto postado", picking.tracking_state_history)

    def test_cancel_is_manual(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        with self.assertRaises(UserError):
            pac.frenet_cancel_shipment(self.env["stock.picking"])

    def test_request_without_token(self):
        self.carrier.frenet_token = False
        with self.assertRaisesRegex(UserError, "token"):
            self.carrier._frenet_request("GET", "/shipping/info")

    @mute_logger(MODEL_LOGGER)
    def test_request_connection_error(self):
        with patch(REQUESTS, side_effect=requests.RequestException("down")):
            with self.assertRaisesRegex(UserError, "Frenet"):
                self.carrier._frenet_request("GET", "/shipping/info")

    def test_sync_services_none_enabled(self):
        with patch(REQUESTS, return_value=FakeResponse({})):
            with self.assertRaisesRegex(UserError, "No shipping service"):
                self.carrier.action_frenet_sync_services()

    def test_rate_shipment_not_synchronized(self):
        rate = self.carrier.frenet_rate_shipment(self.order)
        self.assertFalse(rate["success"])
        self.assertIn("Synchronize", rate["error_message"])

    @mute_logger(MODEL_LOGGER)
    def test_rate_shipment_connection_error(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        with patch(REQUESTS, side_effect=requests.RequestException("down")):
            rate = pac.frenet_rate_shipment(self.order)
        self.assertFalse(rate["success"])
        self.assertIn("Frenet", rate["error_message"])

    def test_event_datetime_malformed(self):
        carrier_model = self.env["delivery.carrier"]
        self.assertEqual(
            carrier_model._frenet_event_datetime({"EventDateTime": "soon"}),
            datetime.min,
        )
        self.assertEqual(carrier_model._frenet_event_datetime({}), datetime.min)

    def test_send_shipping_and_tracking_edges(self):
        pac = self._sync().filtered(lambda c: c.frenet_service_code == "03298")
        self.order.carrier_id = pac
        self.order.action_confirm()
        picking = self.order.picking_ids[0]
        # The public API has no shipment registration: no price, no number
        self.assertEqual(
            pac.frenet_send_shipping(picking),
            [{"exact_price": 0.0, "tracking_number": False}],
        )
        # Without a tracking reference there is no link and no API call
        self.assertFalse(pac.frenet_get_tracking_link(picking))
        with patch(REQUESTS) as request:
            pac.frenet_tracking_state_update(picking)
        request.assert_not_called()
        # Without the carrier code there is no link either
        picking.carrier_tracking_ref = "BR267566353956A"
        pac.frenet_carrier_code = False
        self.assertFalse(pac.frenet_get_tracking_link(picking))
        # Tracking without events keeps the picking untouched
        with patch(REQUESTS, return_value=FakeResponse({"TrackingEvents": []})):
            pac.frenet_tracking_state_update(picking)
        self.assertFalse(picking.tracking_state)
