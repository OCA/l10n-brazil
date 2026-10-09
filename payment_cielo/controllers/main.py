# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class CieloController(http.Controller):
    @http.route("/payment/cielo/payment", type="json", auth="public")
    def cielo_payment(self, reference, partner_id, access_token, card_data):
        """Make a payment request and handle the response.

        :param str reference: The reference of the transaction.
        :param int partner_id: The partner making the transaction, as a
                               `res.partner` id.
        :param str access_token: The access token used to verify the values.
        :param dict card_data: The card details entered in the inline form.
        :return: None
        :raise ValidationError: If the access token is invalid.
        """
        # Check that the transaction details have not been altered.
        if not payment_utils.check_access_token(access_token, reference, partner_id):
            raise ValidationError(_("Cielo: Received tampered payment request data."))

        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference)], limit=1)
        )
        if not tx_sudo:
            raise ValidationError(
                _("Cielo: No transaction found matching reference %s.", reference)
            )

        # Make the payment request to Cielo and handle its response. The card
        # details are only forwarded to Cielo: they never reach the database.
        response_content = tx_sudo._cielo_create_sale(card_data=card_data)
        tx_sudo._handle_notification_data("cielo", {"response": response_content})
