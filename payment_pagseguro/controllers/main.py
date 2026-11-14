# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PagseguroController(http.Controller):
    @http.route("/payment/pagseguro/public_key", type="json", auth="public")
    def pagseguro_public_key(self, provider_id):
        """Return the public key used by the SDK to encrypt the card.

        :param int provider_id: The provider handling the transaction, as a
                                `payment.provider` id.
        :return: The public key of the merchant.
        :rtype: str
        """
        provider_sudo = (
            request.env["payment.provider"].sudo().browse(provider_id).exists()
        )
        if provider_sudo.code != "pagseguro":
            raise ValidationError(_("PagSeguro: The provider is not PagSeguro."))

        response_content = provider_sudo._pagseguro_make_request(
            "/public-keys", {"type": "card"}
        )
        return response_content.get("public_key")

    @http.route("/payment/pagseguro/payment", type="json", auth="public")
    def pagseguro_payment(
        self, reference, partner_id, access_token, encrypted_card, card_holder=None
    ):
        """Make a payment request and handle the response.

        :param str reference: The reference of the transaction.
        :param int partner_id: The partner making the transaction, as a
                               `res.partner` id.
        :param str access_token: The access token used to verify the values.
        :param str encrypted_card: The card encrypted by the PagBank SDK.
        :param str card_holder: The name of the card holder.
        :return: None
        :raise ValidationError: If the access token is invalid.
        """
        if not payment_utils.check_access_token(access_token, reference, partner_id):
            raise ValidationError(
                _("PagSeguro: Received tampered payment request data.")
            )

        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference)], limit=1)
        )
        if not tx_sudo:
            raise ValidationError(
                _("PagSeguro: No transaction found matching reference %s.", reference)
            )

        response_content = tx_sudo._pagseguro_create_order(
            encrypted_card=encrypted_card, card_holder=card_holder
        )
        tx_sudo._handle_notification_data("pagseguro", {"response": response_content})
