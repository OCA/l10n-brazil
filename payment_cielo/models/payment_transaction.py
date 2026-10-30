# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils

from ..const import (
    PAYMENT_STATUS_MAPPING,
    SOFT_DESCRIPTOR_MAX_LENGTH,
    get_card_brand,
)
from ..utils import redact_card_data

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # === BUSINESS METHODS === #

    def _get_specific_processing_values(self, processing_values):
        """Override of `payment` to return an access token as processing values.

        The access token allows the inline form to prove that the payment values
        it sends back to the `/payment/cielo/payment` route were not tampered
        with.

        Note: self.ensure_one() from `_get_processing_values`
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "cielo":
            return res

        return {
            "access_token": payment_utils.generate_access_token(
                processing_values["reference"], processing_values["partner_id"]
            )
        }

    def _send_payment_request(self):
        """Override of `payment` to send a payment request to Cielo.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != "cielo":
            return

        if not self.token_id:
            raise UserError(_("Cielo: The transaction is not linked to a token."))

        response_content = self._cielo_create_sale()
        self._handle_notification_data("cielo", {"response": response_content})

    def _cielo_create_sale(self, card_data=None):
        """Create the sale on Cielo and return the content of the response.

        The card is charged right away unless the provider is configured for
        manual capture, in which case the payment is only authorized. Validation
        transactions are always authorized only, as they are voided afterwards.

        :param dict card_data: The card details of a direct payment, with the
                               keys `card_number`, `card_holder`, `card_expiry`
                               and `card_verification_code`.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        """
        self.ensure_one()

        capture = (
            not self.provider_id.capture_manually and self.operation != "validation"
        )
        payload = {
            "MerchantOrderId": self.reference[:50],
            "Customer": {"Name": self.partner_id.name or ""},
            "Payment": {
                "Type": "CreditCard",
                "Amount": payment_utils.to_minor_currency_units(
                    self.amount, self.currency_id
                ),
                "Installments": 1,
                "Capture": capture,
                "CreditCard": self._cielo_prepare_card_payload(card_data),
            },
        }
        if self.partner_id.email:
            payload["Customer"]["Email"] = self.partner_id.email
        soft_descriptor = self.provider_id.cielo_soft_descriptor
        if soft_descriptor:
            payload["Payment"]["SoftDescriptor"] = soft_descriptor[
                :SOFT_DESCRIPTOR_MAX_LENGTH
            ]

        response_content = self.provider_id._cielo_make_request("/1/sales", payload)
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(redact_card_data(response_content)),
        )
        return response_content

    def _cielo_prepare_card_payload(self, card_data=None):
        """Return the `CreditCard` part of the payload of a sale.

        Either the card details of a direct payment or the card token of the
        token linked to the transaction are sent. The card number never reaches
        the database: Cielo returns a card token that is saved instead, when the
        customer asked for their card to be saved.

        :param dict card_data: The card details of a direct payment.
        :return: The `CreditCard` payload.
        :rtype: dict
        :raise ValidationError: If neither card details nor a token are provided.
        """
        self.ensure_one()

        if card_data:
            card_number = (card_data.get("card_number") or "").replace(" ", "")
            brand = get_card_brand(card_number)
            if not brand:
                raise ValidationError(
                    _("Cielo: The brand of the card is not supported.")
                )
            return {
                "CardNumber": card_number,
                "Holder": card_data.get("card_holder") or "",
                "ExpirationDate": self._cielo_format_expiration_date(
                    card_data.get("card_expiry")
                ),
                "SecurityCode": card_data.get("card_verification_code") or "",
                "Brand": brand,
                "SaveCard": bool(self.tokenize),
            }
        elif self.token_id:
            return {
                "CardToken": self.token_id.provider_ref,
                "Brand": self.token_id.cielo_card_brand,
            }
        raise ValidationError(
            _("Cielo: No card details nor card token to process the payment with.")
        )

    @staticmethod
    def _cielo_format_expiration_date(card_expiry):
        """Return the expiration date in the `MM/YYYY` format expected by Cielo.

        Both `MM/YY` and `MM/YYYY` are accepted, with or without spaces.

        :param str card_expiry: The expiration date of the card.
        :return: The formatted expiration date.
        :rtype: str
        :raise ValidationError: If the expiration date cannot be parsed.
        """
        digits = "".join(char for char in (card_expiry or "") if char.isdigit())
        if len(digits) not in (4, 6):
            raise ValidationError(
                _("Cielo: The expiration date of the card is invalid.")
            )

        month, year = digits[:2], digits[2:]
        if len(year) == 2:
            year = f"20{year}"
        if not 1 <= int(month) <= 12:
            raise ValidationError(
                _("Cielo: The expiration date of the card is invalid.")
            )
        return f"{month}/{year}"

    def _send_capture_request(self):
        """Override of `payment` to send a capture request to Cielo.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_capture_request()
        if self.provider_code != "cielo":
            return

        minor_units = payment_utils.to_minor_currency_units(
            self.amount, self.currency_id
        )
        response_content = self.provider_id._cielo_make_request(
            f"/1/sales/{self.provider_reference}/capture?amount={minor_units}",
            method="PUT",
        )
        _logger.info(
            "capture request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(redact_card_data(response_content)),
        )
        self._handle_notification_data("cielo", {"response": response_content})

    def _send_void_request(self):
        """Override of `payment` to send a void request to Cielo.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_void_request()
        if self.provider_code != "cielo":
            return

        response_content = self._cielo_void()
        self._handle_notification_data("cielo", {"response": response_content})

    def _send_refund_request(self, amount_to_refund=None):
        """Override of `payment` to send a refund request to Cielo.

        Cielo refunds a captured payment with the very same endpoint used to
        void an authorization.

        :param float amount_to_refund: The amount to refund.
        :return: The refund transaction created to process the refund request.
        :rtype: recordset of `payment.transaction`
        """
        if self.provider_code != "cielo":
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        response_content = self._cielo_void(amount=refund_tx.amount)
        refund_tx._handle_notification_data("cielo", {"response": response_content})
        return refund_tx

    def _cielo_void(self, amount=None):
        """Void or refund the payment on Cielo and return the response content.

        :param float amount: The amount to void, in the currency of the
                             transaction. The whole payment is voided if omitted.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        """
        self.ensure_one()

        endpoint = f"/1/sales/{self.provider_reference}/void"
        if amount is not None:
            minor_units = payment_utils.to_minor_currency_units(
                abs(amount), self.currency_id
            )
            endpoint = f"{endpoint}?amount={minor_units}"
        response_content = self.provider_id._cielo_make_request(endpoint, method="PUT")
        _logger.info(
            "void request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(redact_card_data(response_content)),
        )
        return response_content

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on Cielo data.

        :param str provider_code: The code of the provider that handled the tx.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If no transaction is found matching the data.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "cielo" or len(tx) == 1:
            return tx

        reference = notification_data.get("reference") or notification_data.get(
            "response", {}
        ).get("MerchantOrderId")
        if not reference:
            raise ValidationError(_("Cielo: Received data with missing reference."))
        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", "cielo")]
        )
        if not tx:
            raise ValidationError(
                _("Cielo: No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the transaction based on Cielo data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "cielo":
            return

        response_content = notification_data.get("response") or {}
        # Sales are answered with the payment wrapped in a `Payment` key, while
        # capture and void requests answer with the payment itself.
        payment_data = response_content.get("Payment", response_content)

        payment_id = payment_data.get("PaymentId")
        if payment_id:
            self.provider_reference = payment_id

        status = payment_data.get("Status")
        if status is None:
            raise ValidationError(_("Cielo: Received data with missing status."))

        state_message = payment_data.get("ReturnMessage") or payment_data.get(
            "ReasonMessage"
        )
        if status in PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending(state_message=state_message)
        elif status in PAYMENT_STATUS_MAPPING["authorized"]:
            self._cielo_tokenize_from_notification_data(payment_data)
            if self.operation == "validation":
                self._set_authorized(state_message=state_message)
                self._send_void_request()  # Last, as it processes the response.
            elif self.provider_id.capture_manually:
                self._set_authorized(state_message=state_message)
            else:  # The capture requested along with the sale did not go through.
                self._set_error(
                    _(
                        "Cielo: The payment was authorized but could not be "
                        "captured: %s",
                        state_message or _("no information given"),
                    )
                )
        elif status in PAYMENT_STATUS_MAPPING["done"]:
            self._cielo_tokenize_from_notification_data(payment_data)
            self._set_done(state_message=state_message)
            if self.operation == "refund":
                # Post-process the refund now: no customer browses its portal page.
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        elif status in PAYMENT_STATUS_MAPPING["cancel"]:
            if self.operation == "refund":
                self._set_done(state_message=state_message)
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
            elif self.operation == "validation" and self.state == "authorized":
                # The validation authorization was voided as expected.
                self._set_done(state_message=state_message)
            else:
                self._set_canceled(state_message=state_message)
        elif status in PAYMENT_STATUS_MAPPING["error"]:
            _logger.warning(
                "received data with status %(status)s for transaction with reference "
                "%(ref)s: %(message)s",
                {"status": status, "ref": self.reference, "message": state_message},
            )
            self._set_error(
                _(
                    "Cielo: The payment was refused with the following information: %s",
                    state_message or _("no information given"),
                )
            )
        else:
            _logger.warning(
                "received data with invalid status %(status)s for transaction with "
                "reference %(ref)s",
                {"status": status, "ref": self.reference},
            )
            self._set_error(_("Cielo: Received data with invalid status: %s", status))

    def _cielo_tokenize_from_notification_data(self, payment_data):
        """Create a token from the card token returned by Cielo, if requested.

        Note: self.ensure_one()

        :param dict payment_data: The payment part of the notification data.
        :return: None
        """
        self.ensure_one()

        if not self.tokenize or self.token_id:
            return

        card_data = payment_data.get("CreditCard") or {}
        card_token = card_data.get("CardToken")
        if not card_token:
            _logger.warning(
                "tokenization was requested but Cielo did not return a card token "
                "for transaction with reference %s",
                self.reference,
            )
            return

        token = self.env["payment.token"].create(
            {
                "provider_id": self.provider_id.id,
                "payment_details": (card_data.get("CardNumber") or "")[-4:],
                "partner_id": self.partner_id.id,
                "provider_ref": card_token,
                "cielo_card_brand": card_data.get("Brand"),
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
