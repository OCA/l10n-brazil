# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint
import re

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils

from ..const import PAYMENT_STATUS_MAPPING, SOFT_DESCRIPTOR_MAX_LENGTH
from ..utils import redact_card_data

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # === BUSINESS METHODS === #

    def _get_specific_processing_values(self, processing_values):
        """Override of `payment` to return an access token as processing values.

        Note: self.ensure_one() from `_get_processing_values`
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "pagseguro":
            return res

        return {
            "access_token": payment_utils.generate_access_token(
                processing_values["reference"], processing_values["partner_id"]
            )
        }

    def _send_payment_request(self):
        """Override of `payment` to send a payment request to PagBank.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != "pagseguro":
            return

        if not self.token_id:
            raise UserError(_("PagSeguro: The transaction is not linked to a token."))

        response_content = self._pagseguro_create_order()
        self._handle_notification_data("pagseguro", {"response": response_content})

    def _pagseguro_create_order(self, encrypted_card=None, card_holder=None):
        """Create the order and its charge on PagBank.

        The charge is captured right away unless the provider is configured for
        manual capture. Validation transactions are only authorized, as they are
        canceled afterwards.

        :param str encrypted_card: The card encrypted by the PagBank SDK in the
                                   browser, for a direct payment.
        :param str card_holder: The name of the card holder, as typed in the
                                inline form.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        """
        self.ensure_one()

        amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        capture = (
            not self.provider_id.capture_manually and self.operation != "validation"
        )
        payload = {
            "reference_id": self.reference,
            "customer": self._pagseguro_prepare_customer_payload(),
            "items": [
                {
                    "reference_id": self.reference,
                    "name": self.reference,
                    "quantity": 1,
                    "unit_amount": amount,
                }
            ],
            "charges": [
                {
                    "reference_id": self.reference,
                    "description": self.reference[:64],
                    "amount": {"value": amount, "currency": "BRL"},
                    "payment_method": {
                        "type": "CREDIT_CARD",
                        "installments": 1,
                        "capture": capture,
                        "soft_descriptor": self._pagseguro_get_soft_descriptor(),
                        "card": self._pagseguro_prepare_card_payload(
                            encrypted_card, card_holder
                        ),
                    },
                }
            ],
        }

        response_content = self.provider_id._pagseguro_make_request("/orders", payload)
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(self._pagseguro_filter_response(response_content)),
        )
        return response_content

    def _pagseguro_prepare_customer_payload(self):
        """Return the `customer` part of the payload of an order.

        :return: The customer payload.
        :rtype: dict
        """
        self.ensure_one()

        customer = {"name": self.partner_name or self.partner_id.name or ""}
        if self.partner_email:
            customer["email"] = self.partner_email
        tax_id = re.sub(r"\D", "", self.partner_id.vat or "")
        if tax_id:
            customer["tax_id"] = tax_id
        return customer

    def _pagseguro_prepare_card_payload(self, encrypted_card=None, card_holder=None):
        """Return the `card` part of the payload of a charge.

        Either the card encrypted by the SDK in the browser or the card saved on
        the PagBank side is sent. The card number never reaches the database.

        :param str encrypted_card: The card encrypted by the PagBank SDK.
        :param str card_holder: The name of the card holder.
        :return: The card payload.
        :rtype: dict
        :raise ValidationError: If neither an encrypted card nor a token exist.
        """
        self.ensure_one()

        if encrypted_card:
            card = {"encrypted": encrypted_card, "store": bool(self.tokenize)}
            if card_holder:
                card["holder"] = {"name": card_holder}
            return card
        elif self.token_id:
            return {"id": self.token_id.provider_ref}
        raise ValidationError(
            _("PagSeguro: No card nor card token to process the payment with.")
        )

    def _pagseguro_get_soft_descriptor(self):
        """Return the soft descriptor of the charge, truncated for PagBank.

        :return: The soft descriptor.
        :rtype: str
        """
        self.ensure_one()

        soft_descriptor = (
            self.provider_id.pagseguro_soft_descriptor
            or self.provider_id.company_id.name
            or ""
        )
        return soft_descriptor[:SOFT_DESCRIPTOR_MAX_LENGTH]

    def _send_capture_request(self):
        """Override of `payment` to send a capture request to PagBank.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_capture_request()
        if self.provider_code != "pagseguro":
            return

        amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        response_content = self.provider_id._pagseguro_make_request(
            f"/charges/{self.provider_reference}/capture",
            {"amount": {"value": amount, "currency": "BRL"}},
        )
        _logger.info(
            "capture request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(self._pagseguro_filter_response(response_content)),
        )
        self._handle_notification_data("pagseguro", {"response": response_content})

    def _send_void_request(self):
        """Override of `payment` to send a void request to PagBank.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_void_request()
        if self.provider_code != "pagseguro":
            return

        response_content = self._pagseguro_cancel()
        self._handle_notification_data("pagseguro", {"response": response_content})

    def _send_refund_request(self, amount_to_refund=None):
        """Override of `payment` to send a refund request to PagBank.

        PagBank refunds a captured charge with the same endpoint used to void an
        authorization.

        :param float amount_to_refund: The amount to refund.
        :return: The refund transaction created to process the refund request.
        :rtype: recordset of `payment.transaction`
        """
        if self.provider_code != "pagseguro":
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        response_content = self._pagseguro_cancel(amount=refund_tx.amount)
        refund_tx._handle_notification_data("pagseguro", {"response": response_content})
        return refund_tx

    def _pagseguro_cancel(self, amount=None):
        """Cancel or refund the charge on PagBank and return the response.

        :param float amount: The amount to cancel, in the currency of the
                             transaction. The whole charge is canceled if
                             omitted.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        """
        self.ensure_one()

        payload = None
        if amount is not None:
            payload = {
                "amount": {
                    "value": payment_utils.to_minor_currency_units(
                        abs(amount), self.currency_id
                    ),
                    "currency": "BRL",
                }
            }
        response_content = self.provider_id._pagseguro_make_request(
            f"/charges/{self.provider_reference}/cancel", payload
        )
        _logger.info(
            "cancel request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(self._pagseguro_filter_response(response_content)),
        )
        return response_content

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on PagBank data.

        :param str provider_code: The code of the provider that handled the tx.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If no transaction is found matching the data.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "pagseguro" or len(tx) == 1:
            return tx

        reference = notification_data.get("reference") or notification_data.get(
            "response", {}
        ).get("reference_id")
        if not reference:
            raise ValidationError(_("PagSeguro: Received data with missing reference."))
        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", "pagseguro")]
        )
        if not tx:
            raise ValidationError(
                _("PagSeguro: No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the transaction based on PagBank data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "pagseguro":
            return

        charge_data = self._pagseguro_get_charge_data(notification_data)
        if not charge_data:
            raise ValidationError(_("PagSeguro: Received data without any charge."))

        if charge_data.get("id"):
            self.provider_reference = charge_data["id"]

        status = charge_data.get("status")
        if not status:
            raise ValidationError(_("PagSeguro: Received data with missing status."))

        payment_response = charge_data.get("payment_response") or {}
        state_message = payment_response.get("message")
        if status in PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending(state_message=state_message)
        elif status in PAYMENT_STATUS_MAPPING["authorized"]:
            self._pagseguro_tokenize_from_notification_data(charge_data)
            self._set_authorized(state_message=state_message)
            if self.operation == "validation":
                self._send_void_request()  # Last, as it processes the response.
        elif status in PAYMENT_STATUS_MAPPING["done"]:
            self._pagseguro_tokenize_from_notification_data(charge_data)
            self._set_done(state_message=state_message)
            if self.operation == "refund":
                # Post-process now: no customer browses the portal page.
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        elif status in PAYMENT_STATUS_MAPPING["cancel"]:
            if self.operation == "refund":
                self._set_done(state_message=state_message)
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
            elif self.operation == "validation" and self.state == "authorized":
                self._set_done(state_message=state_message)
            else:
                self._set_canceled(state_message=state_message)
        elif status in PAYMENT_STATUS_MAPPING["error"]:
            _logger.warning(
                "received data with status %(status)s for transaction with "
                "reference %(ref)s: %(message)s",
                {"status": status, "ref": self.reference, "message": state_message},
            )
            self._set_error(
                _(
                    "PagSeguro: The payment was refused with the following "
                    "information: %s",
                    state_message or _("no information given"),
                )
            )
        else:
            _logger.warning(
                "received data with invalid status %(status)s for transaction "
                "with reference %(ref)s",
                {"status": status, "ref": self.reference},
            )
            self._set_error(
                _("PagSeguro: Received data with invalid status: %s", status)
            )

    @staticmethod
    def _pagseguro_get_charge_data(notification_data):
        """Return the charge of the notification data.

        Orders are answered with a list of charges, while capture and cancel
        requests answer with the charge itself.

        :param dict notification_data: The notification data sent by the provider.
        :return: The charge data.
        :rtype: dict
        """
        response_content = notification_data.get("response") or {}
        charges = response_content.get("charges")
        if charges:
            return charges[0]
        if response_content.get("status"):
            return response_content
        return {}

    def _pagseguro_tokenize_from_notification_data(self, charge_data):
        """Create a token from the card saved by PagBank, if it was requested.

        Note: self.ensure_one()

        :param dict charge_data: The charge of the notification data.
        :return: None
        """
        self.ensure_one()

        if not self.tokenize or self.token_id:
            return

        card_data = (charge_data.get("payment_method") or {}).get("card") or {}
        card_id = card_data.get("id")
        if not card_id:
            _logger.warning(
                "tokenization was requested but PagBank did not return a card id "
                "for transaction with reference %s",
                self.reference,
            )
            return

        token = self.env["payment.token"].create(
            {
                "provider_id": self.provider_id.id,
                "payment_details": card_data.get("last_digits"),
                "partner_id": self.partner_id.id,
                "provider_ref": card_id,
                "pagseguro_card_brand": card_data.get("brand"),
                "verified": True,
            }
        )
        self.write({"token_id": token.id, "tokenize": False})
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s "
            "from transaction with reference %(ref)s",
            {
                "token_id": token.id,
                "partner_id": self.partner_id.id,
                "ref": self.reference,
            },
        )

    @staticmethod
    def _pagseguro_filter_response(response):
        """Return the response without the payment details, to be logged.

        :param dict response: The response of a request.
        :return: The response without its sensitive parts.
        :rtype: dict
        """
        if not isinstance(response, dict):
            return response
        filtered_response = dict(response)
        for key in ("links", "metadata", "notification_urls", "customer"):
            filtered_response.pop(key, None)
        return redact_card_data(filtered_response)
