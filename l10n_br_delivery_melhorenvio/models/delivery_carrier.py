# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import fields, models
from odoo.exceptions import UserError

MELHORENVIO_TRACKING_URL = "https://www.melhorrastreio.com.br/rastreio"
# Shipment status at Melhor Envio -> delivery_state of the picking.
MELHORENVIO_DELIVERY_STATES = {
    "pending": "shipping_recorded_in_carrier",
    "released": "shipping_recorded_in_carrier",
    "generated": "shipping_recorded_in_carrier",
    "posted": "in_transit",
    "delivered": "customer_delivered",
    "undelivered": "incident",
    "canceled": "canceled_shipment",
    "expired": "canceled_shipment",
}
# Melhor Envio refuses a quote without weight.
MINIMUM_WEIGHT_KG = 0.05


def _digits(value):
    return re.sub(r"\D", "", value or "")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("melhorenvio", "Melhor Envio")],
        ondelete={
            "melhorenvio": lambda records: records.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    melhorenvio_account_id = fields.Many2one(
        "melhorenvio.account",
        string="Melhor Envio Account",
        check_company=True,
        ondelete="restrict",
    )

    melhorenvio_service_id = fields.Integer(
        string="Melhor Envio Service ID",
        readonly=True,
        help="Filled by the service synchronization.",
    )

    melhorenvio_service_name = fields.Char(string="Melhor Envio Service", readonly=True)

    melhorenvio_company_name = fields.Char(
        string="Melhor Envio Carrier",
        readonly=True,
        help="Carrier that runs this service (e.g. Correios, Jadlog).",
    )

    melhorenvio_agency_id = fields.Integer(
        string="Melhor Envio Agency ID",
        help="Agency where the parcels are dropped, for the carriers that "
        "ask for one (e.g. Jadlog).",
    )

    melhorenvio_package_length = fields.Integer(string="Box Length (cm)", default=20)

    melhorenvio_package_width = fields.Integer(string="Box Width (cm)", default=15)

    melhorenvio_package_height = fields.Integer(string="Box Height (cm)", default=12)

    def _melhorenvio_account(self):
        self.ensure_one()
        account = self.sudo().melhorenvio_account_id
        if not account:
            raise UserError(
                self.env._(
                    "Set the Melhor Envio account of the delivery method %(name)s.",
                    name=self.name,
                )
            )
        if not self.melhorenvio_service_id:
            raise UserError(
                self.env._(
                    "Synchronize the services of the Melhor Envio account first."
                )
            )
        return account

    def _melhorenvio_request(self, method, endpoint, payload=None):
        return self._melhorenvio_account()._request(method, endpoint, payload)

    # ------------------------------------------------------------------
    # Quotation
    # ------------------------------------------------------------------

    def _melhorenvio_quote_payload(self, order):
        self.ensure_one()
        lines = order.order_line.filtered(
            lambda line: not line.display_type
            and not line.is_delivery
            and line.product_id.type != "service"
        )
        weight = sum(line.product_id.weight * line.product_uom_qty for line in lines)
        value = sum(lines.mapped("price_total"))
        origin = order.warehouse_id.partner_id or order.company_id.partner_id
        # The order ships in a single box, configured on the delivery method.
        return {
            "from": {"postal_code": _digits(origin.zip)},
            "to": {"postal_code": _digits(order.partner_shipping_id.zip)},
            "products": [
                {
                    "id": order.name,
                    "width": self.melhorenvio_package_width,
                    "height": self.melhorenvio_package_height,
                    "length": self.melhorenvio_package_length,
                    "weight": max(weight, MINIMUM_WEIGHT_KG),
                    "insurance_value": round(value, 2),
                    "quantity": 1,
                }
            ],
            "services": str(self.melhorenvio_service_id),
        }

    def melhorenvio_rate_shipment(self, order):
        self.ensure_one()

        def error(message):
            return {
                "success": False,
                "price": 0.0,
                "error_message": message,
                "warning_message": False,
            }

        payload = self._melhorenvio_quote_payload(order)
        if len(payload["to"]["postal_code"]) != 8:
            return error(self.env._("Set the ZIP code of the delivery address."))
        if len(payload["from"]["postal_code"]) != 8:
            return error(self.env._("Set the ZIP code of the warehouse address."))
        try:
            result = self._melhorenvio_request(
                "POST", "/api/v2/me/shipment/calculate", payload
            )
        except UserError as user_error:
            return error(str(user_error))
        if isinstance(result, dict):
            result = [result]
        service = next(
            (item for item in result if item.get("id") == self.melhorenvio_service_id),
            {},
        )
        if not service or service.get("error"):
            return error(
                service.get("error")
                or self.env._("Service unavailable for this address.")
            )
        price = service.get("custom_price") or service.get("price")
        delivery_time = int(
            service.get("custom_delivery_time") or service.get("delivery_time") or 0
        )
        return {
            "success": True,
            "price": float(price),
            "error_message": False,
            "warning_message": delivery_time
            and self.env._(
                "Estimated delivery: %(days)s working day(s).", days=delivery_time
            ),
        }

    # ------------------------------------------------------------------
    # Label
    # ------------------------------------------------------------------

    def _melhorenvio_party(self, partner):
        """Sender or recipient of the label. Melhor Envio wants the CPF in
        `document` and the CNPJ in `company_document`."""
        commercial = partner.commercial_partner_id
        document = _digits(partner.vat or commercial.vat)
        party = {
            "name": (partner.name or commercial.name or "")[:100],
            "phone": _digits(partner.phone or partner.mobile),
            "address": partner.street_name or partner.street or "",
            "number": partner.street_number or "S/N",
            "complement": partner.street2 or "",
            "district": partner.district or "",
            "city": partner.city_id.name or partner.city or "",
            "state_abbr": partner.state_id.code or "",
            "country_id": partner.country_id.code or "BR",
            "postal_code": _digits(partner.zip),
        }
        if len(document) == 14:
            party["company_document"] = document
        elif document:
            party["document"] = document
        missing = [
            label
            for key, label in (
                ("address", self.env._("street")),
                ("city", self.env._("city")),
                ("postal_code", self.env._("ZIP code")),
            )
            if not party[key]
        ]
        if not document:
            missing.append(self.env._("CPF or CNPJ"))
        if missing:
            raise UserError(
                self.env._(
                    "%(partner)s: fill %(fields)s before buying the label.",
                    partner=partner.display_name,
                    fields=", ".join(missing),
                )
            )
        return party

    def _melhorenvio_invoice_key(self, picking):
        """Access key of the authorized NF-e of the delivery, when there is
        one. Without it the shipment goes with a content declaration."""
        invoices = picking.sale_id.invoice_ids.filtered(
            lambda move: move.state == "posted" and move.move_type == "out_invoice"
        )
        for document in invoices.fiscal_document_id:
            key = _digits(document.document_key)
            if (
                len(key) == 44
                and document.document_type == "55"
                and document.state_edoc == "autorizada"
            ):
                return key
        return False

    def _melhorenvio_cart_payload(self, picking):
        self.ensure_one()
        sender = picking.picking_type_id.warehouse_id.partner_id
        products = []
        value = 0.0
        for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
            quantity = move.quantity or move.product_uom_qty
            if not quantity:
                continue
            price = (
                move.sale_line_id.price_reduce_taxinc
                if move.sale_line_id
                else move.product_id.lst_price
            )
            value += price * quantity
            products.append(
                {
                    "name": (move.product_id.name or "")[:100],
                    "quantity": f"{quantity:g}",
                    "unitary_value": f"{price:.2f}",
                }
            )
        if not products:
            raise UserError(
                self.env._("The delivery %(name)s has no product.", name=picking.name)
            )
        options = {
            "insurance_value": round(value, 2),
            "receipt": False,
            "own_hand": False,
            "reverse": False,
            "non_commercial": True,
            "platform": "Odoo",
            "tags": [{"tag": picking.name, "url": None}],
        }
        invoice_key = self._melhorenvio_invoice_key(picking)
        if invoice_key:
            options["non_commercial"] = False
            options["invoice"] = {"key": invoice_key}
        payload = {
            "service": self.melhorenvio_service_id,
            "from": self._melhorenvio_party(sender or picking.company_id.partner_id),
            "to": self._melhorenvio_party(picking.partner_id),
            "products": products,
            "volumes": [
                {
                    "height": self.melhorenvio_package_height,
                    "width": self.melhorenvio_package_width,
                    "length": self.melhorenvio_package_length,
                    "weight": max(
                        picking.shipping_weight or picking.weight, MINIMUM_WEIGHT_KG
                    ),
                }
            ],
            "options": options,
        }
        if self.melhorenvio_agency_id:
            payload["agency"] = self.melhorenvio_agency_id
        return payload

    def _melhorenvio_label_url(self, picking):
        result = self._melhorenvio_request(
            "POST",
            "/api/v2/me/shipment/print",
            {"mode": "public", "orders": [picking.melhorenvio_order_id]},
        )
        return result.get("url")

    def _melhorenvio_buy_label(self, picking):
        """Cart, checkout (paid with the wallet balance), generation and
        print link.

        Once the cart entry exists, a failing step does not raise: the
        delivery keeps the Melhor Envio order and a new attempt resumes it,
        reading its status at Melhor Envio before paying."""
        self.ensure_one()
        price = picking.carrier_price
        if picking.melhorenvio_order_id:
            order = self._melhorenvio_request(
                "GET", f"/api/v2/me/orders/{picking.melhorenvio_order_id}"
            )
            picking.melhorenvio_status = order.get("status")
            price = float(order.get("price") or price)
        else:
            cart = self._melhorenvio_request(
                "POST", "/api/v2/me/cart", self._melhorenvio_cart_payload(picking)
            )
            picking.write(
                {
                    "melhorenvio_order_id": cart["id"],
                    "melhorenvio_protocol": cart.get("protocol"),
                    "melhorenvio_status": cart.get("status"),
                }
            )
        orders = {"orders": [picking.melhorenvio_order_id]}
        tracking = False
        try:
            if picking.melhorenvio_status == "pending":
                with self.env.cr.savepoint():
                    purchase = self._melhorenvio_request(
                        "POST", "/api/v2/me/shipment/checkout", orders
                    ).get("purchase", {})
                    bought = next(
                        (
                            item
                            for item in purchase.get("orders", [])
                            if item.get("id") == picking.melhorenvio_order_id
                        ),
                        {},
                    )
                    price = float(bought.get("price") or purchase.get("total") or 0.0)
                    picking.melhorenvio_status = bought.get("status") or "released"
            with self.env.cr.savepoint():
                self._melhorenvio_request(
                    "POST", "/api/v2/me/shipment/generate", orders
                )
                picking.melhorenvio_label_url = self._melhorenvio_label_url(picking)
            tracking = self._melhorenvio_tracking(picking)
        except UserError as error:
            picking.message_post(
                body=self.env._(
                    "The Melhor Envio label is not finished: %(error)s "
                    "Buy it again to resume; a paid label is not paid twice.",
                    error=error,
                )
            )
            return {"exact_price": price, "tracking_number": False}
        picking.message_post(
            body=self.env._(
                "Melhor Envio label bought: %(protocol)s, %(service)s, "
                "R$ %(price).2f.",
                protocol=picking.melhorenvio_protocol,
                service=self.name,
                price=price,
            )
        )
        return {"exact_price": price, "tracking_number": tracking}

    # ------------------------------------------------------------------
    # Shipping and tracking
    # ------------------------------------------------------------------

    def melhorenvio_send_shipping(self, pickings):
        return [self._melhorenvio_buy_label(picking) for picking in pickings]

    def melhorenvio_get_tracking_link(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return False
        return f"{MELHORENVIO_TRACKING_URL}/{picking.carrier_tracking_ref}"

    def melhorenvio_cancel_shipment(self, pickings):
        for picking in pickings.filtered("melhorenvio_order_id"):
            self._melhorenvio_request(
                "POST",
                "/api/v2/me/shipment/cancel",
                {
                    "order": {
                        "id": picking.melhorenvio_order_id,
                        "reason_id": "2",
                        "description": f"Cancelado pelo Odoo ({picking.name})",
                    }
                },
            )
            picking.write(
                {
                    "melhorenvio_status": "canceled",
                    "carrier_tracking_ref": False,
                    "delivery_state": "canceled_shipment",
                }
            )

    def _melhorenvio_tracking(self, picking):
        """Read the shipment at Melhor Envio, store its status and return
        the tracking code (it only exists after the label is generated)."""
        self.ensure_one()
        result = self._melhorenvio_request(
            "POST",
            "/api/v2/me/shipment/tracking",
            {"orders": [picking.melhorenvio_order_id]},
        )
        shipment = (result or {}).get(picking.melhorenvio_order_id) or {}
        status = shipment.get("status")
        if status:
            picking.write(
                {
                    "melhorenvio_status": status,
                    "tracking_state": status,
                    "delivery_state": MELHORENVIO_DELIVERY_STATES.get(
                        status, picking.delivery_state
                    ),
                }
            )
        tracking = shipment.get("tracking")
        if not tracking:
            # The tracking endpoint only shows the code some time after the
            # label is generated; the order shows it at once.
            order = self._melhorenvio_request(
                "GET", f"/api/v2/me/orders/{picking.melhorenvio_order_id}"
            )
            tracking = order.get("tracking") or order.get("self_tracking")
        return tracking or False

    def melhorenvio_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.melhorenvio_order_id:
            return
        tracking = self._melhorenvio_tracking(picking)
        if tracking and picking.carrier_tracking_ref != tracking:
            picking.carrier_tracking_ref = tracking
