# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from datetime import datetime

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

FRENET_API_URL = "https://api.frenet.com.br"
FRENET_TIMEOUT = 30
FRENET_TRACKING_URL = "https://rastreio.frenet.com.br"
# Below this weight some carriers refuse the quote; Frenet itself quotes
# fractions of kg without problem.
MINIMUM_WEIGHT_KG = 0.05

# EventType of /tracking/trackinginfo -> delivery_state of the picking:
# 0 initial, 1 in transit, 2 delayed, 3 returned, 4 lost, 9 delivered.
EVENT_TYPE_TO_DELIVERY_STATE = {
    "0": "shipping_recorded_in_carrier",
    "1": "in_transit",
    "2": "in_transit",
    "3": "incident",
    "4": "incident",
    "9": "customer_delivered",
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("frenet", "Frenet")],
        ondelete={
            "frenet": lambda records: records.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    frenet_token = fields.Char(
        groups="base.group_system",
        help="Token of the Frenet account, from Painel Frenet > Integrações.",
    )

    frenet_service_code = fields.Char(
        readonly=True,
        help="Code of the shipping service in Frenet (e.g. 03298 for PAC). "
        "Filled by the service synchronization.",
    )

    frenet_service_description = fields.Char(readonly=True)

    frenet_carrier_name = fields.Char(
        string="Frenet Carrier",
        readonly=True,
        help="Carrier that runs this service (e.g. Correios, Jadlog).",
    )

    frenet_carrier_code = fields.Char(
        readonly=True,
        help="Code of the carrier in Frenet, used in the tracking URL.",
    )

    frenet_package_length = fields.Float(
        default=20.0, help="Length in cm of the box the order ships in."
    )

    frenet_package_width = fields.Float(
        default=15.0, help="Width in cm of the box the order ships in."
    )

    frenet_package_height = fields.Float(
        default=12.0, help="Height in cm of the box the order ships in."
    )

    # ------------------------------------------------------------------
    # Frenet API
    # ------------------------------------------------------------------

    def _frenet_request(self, method, endpoint, payload=None):
        self.ensure_one()
        if not self.frenet_token:
            raise UserError(
                _("Set the Frenet token on the delivery method %s.") % self.name
            )
        try:
            response = requests.request(
                method,
                FRENET_API_URL + endpoint,
                json=payload,
                headers={"token": self.frenet_token, "Accept": "application/json"},
                timeout=FRENET_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            _logger.warning("Frenet: %s %s failed: %s", method, endpoint, error)
            raise UserError(
                _("Frenet could not be reached, try again later.")
            ) from error

    @staticmethod
    def _frenet_clean_zip(value):
        return re.sub(r"\D", "", value or "")

    # ------------------------------------------------------------------
    # Service synchronization
    # ------------------------------------------------------------------

    def action_frenet_sync_services(self):
        """Create or update one delivery method per service enabled in the
        Frenet account, so the customer picks the service at the checkout."""
        self.ensure_one()
        info = self._frenet_request("GET", "/shipping/info")
        services = info.get("ShippingSeviceAvailableArray") or []
        if not services:
            raise UserError(_("No shipping service is enabled in Frenet."))
        for service in services:
            values = {
                "frenet_service_code": service["ServiceCode"],
                "frenet_service_description": service["ServiceDescription"],
                "frenet_carrier_name": service["Carrier"],
                "frenet_carrier_code": service.get("CarrierCode"),
            }
            carrier = self.search(
                [
                    ("delivery_type", "=", "frenet"),
                    ("frenet_service_code", "=", service["ServiceCode"]),
                ],
                limit=1,
            )
            if carrier:
                carrier.write(values)
                continue
            self.create(
                {
                    **values,
                    "name": f"{service['Carrier']} {service['ServiceDescription']}",
                    "delivery_type": "frenet",
                    "frenet_token": self.frenet_token,
                    "frenet_package_length": self.frenet_package_length,
                    "frenet_package_width": self.frenet_package_width,
                    "frenet_package_height": self.frenet_package_height,
                    "product_id": self.product_id.id,
                    "company_id": self.company_id.id,
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Frenet Services"),
            "res_model": "delivery.carrier",
            "view_mode": "list,form",
            "domain": [("delivery_type", "=", "frenet")],
        }

    # ------------------------------------------------------------------
    # Quotation
    # ------------------------------------------------------------------

    def _frenet_quote_payload(self, order):
        self.ensure_one()
        lines = order.order_line.filtered(
            lambda line: not line.display_type
            and not line.is_delivery
            and line.product_id.type != "service"
        )
        weight = sum(line.product_id.weight * line.product_uom_qty for line in lines)
        value = sum(lines.mapped("price_total"))
        return {
            "SellerCEP": self._frenet_clean_zip(order.company_id.partner_id.zip),
            "RecipientCEP": self._frenet_clean_zip(order.partner_shipping_id.zip),
            "ShipmentInvoiceValue": round(value, 2),
            "RecipientCountry": "BR",
            "ShippingServiceCode": self.frenet_service_code,
            "ShippingItemArray": [
                {
                    "Length": self.frenet_package_length,
                    "Width": self.frenet_package_width,
                    "Height": self.frenet_package_height,
                    "Weight": max(weight, MINIMUM_WEIGHT_KG),
                    "Quantity": 1,
                }
            ],
        }

    def frenet_rate_shipment(self, order):
        self.ensure_one()

        def error(message):
            return {
                "success": False,
                "price": 0.0,
                "error_message": message,
                "warning_message": False,
            }

        if not self.frenet_service_code:
            return error(_("Synchronize the Frenet services first."))
        payload = self._frenet_quote_payload(order)
        if len(payload["RecipientCEP"]) != 8:
            return error(_("Set the ZIP code of the delivery address."))
        try:
            result = self._frenet_request("POST", "/shipping/quote", payload)
        except UserError as user_error:
            return error(str(user_error))
        service = next(
            (
                item
                for item in result.get("ShippingSevicesArray") or []
                if item.get("ServiceCode") == self.frenet_service_code
            ),
            None,
        )
        if not service or service.get("Error"):
            message = (service or {}).get("Msg") or _(
                "Service unavailable for this address."
            )
            return error(message)
        delivery_time = int(service.get("DeliveryTime") or 0)
        return {
            "success": True,
            "price": float(service["ShippingPrice"]),
            "error_message": False,
            "warning_message": delivery_time
            and _("Estimated delivery: %s working day(s).") % delivery_time,
            "frenet_delivery_time": delivery_time,
        }

    # ------------------------------------------------------------------
    # Shipping and tracking
    # ------------------------------------------------------------------

    def frenet_send_shipping(self, pickings):
        # Frenet's public API does not register the shipment nor emit the
        # transport label: that is done at the Frenet panel, and the
        # tracking number is then typed into the picking.
        return [{"exact_price": 0.0, "tracking_number": False} for _ in pickings]

    def frenet_get_tracking_link(self, picking):
        self.ensure_one()
        if not (self.frenet_carrier_code and picking.carrier_tracking_ref):
            return False
        return (
            f"{FRENET_TRACKING_URL}/{self.frenet_carrier_code}"
            f"/{picking.carrier_tracking_ref}"
        )

    def frenet_cancel_shipment(self, pickings):
        raise UserError(_("Cancel the shipment at the Frenet panel."))

    @staticmethod
    def _frenet_event_datetime(event):
        try:
            return datetime.strptime(event.get("EventDateTime"), "%d/%m/%Y %H:%M")
        except (TypeError, ValueError):
            return datetime.min

    def frenet_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        result = self._frenet_request(
            "POST",
            "/tracking/trackinginfo",
            {
                "ShippingServiceCode": self.frenet_service_code,
                "TrackingNumber": picking.carrier_tracking_ref,
                "OrderNumber": picking.sale_id.name or picking.name,
            },
        )
        events = result.get("TrackingEvents") or []
        if not events:
            return
        picking.tracking_state_history = "\n".join(
            "{EventDateTime} - {EventDescription} ({EventLocation})".format(
                **{
                    key: event.get(key) or ""
                    for key in (
                        "EventDateTime",
                        "EventDescription",
                        "EventLocation",
                    )
                }
            )
            for event in events
        )
        latest = max(events, key=self._frenet_event_datetime)
        picking.tracking_state = (
            f"{latest.get('EventDateTime')} - {latest.get('EventDescription')}"
        )
        picking.delivery_state = EVENT_TYPE_TO_DELIVERY_STATE.get(
            str(latest.get("EventType")), "in_transit"
        )
