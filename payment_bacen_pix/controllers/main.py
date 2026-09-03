# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment import utils as payment_utils

from ..utils import redact_personal_data

_logger = logging.getLogger(__name__)


class BacenPixController(http.Controller):
    @http.route(
        "/payment/bacenpix/qrcode",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
        website=True,
    )
    def bacenpix_qrcode(self, reference, access_token, **kwargs):
        """Render the page holding the QR code of the charge.

        :param str reference: The reference of the transaction.
        :param str access_token: The access token used to verify the values.
        :return: The rendered page.
        """
        tx_sudo = self._bacenpix_get_transaction(reference, access_token)
        return request.render(
            "payment_bacen_pix.qrcode_page",
            {
                "tx": tx_sudo,
                "access_token": access_token,
                "qr_code": tx_sudo.bacenpix_qrcode,
            },
        )

    @http.route("/payment/bacenpix/status", type="json", auth="public")
    def bacenpix_status(self, reference, access_token):
        """Query the charge on the PSP and return the state of the transaction.

        The page holding the QR code polls this route, which is what makes the
        payment be seen without the webhook of the arrangement.

        :param str reference: The reference of the transaction.
        :param str access_token: The access token used to verify the values.
        :return: The state of the transaction.
        :rtype: dict
        """
        tx_sudo = self._bacenpix_get_transaction(reference, access_token)
        if tx_sudo.state in ("draft", "pending"):
            tx_sudo._bacenpix_poll_charge()
        return {"state": tx_sudo.state}

    @http.route("/payment/bacenpix/webhook", type="json", auth="public", csrf=False)
    def bacenpix_webhook(self):
        """Process the notification sent by the PSP when a charge is paid.

        The PSP posts the payments it received, each one holding the txid of its
        charge. See the `/webhook` section of the Pix API.

        :return: An empty acknowledgement, as expected by the arrangement.
        :rtype: dict
        """
        notification_data = request.get_json_data()
        _logger.info(
            "notification received from Pix:\n%s",
            pprint.pformat(redact_personal_data(notification_data)),
        )

        payments = (notification_data or {}).get("pix") or []
        for payment in payments:
            txid = payment.get("txid")
            if not txid:
                continue
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                .search([("bacenpix_txid", "=", txid)], limit=1)
            )
            if not tx_sudo:
                _logger.warning("no transaction found matching txid %s", txid)
                continue
            # The notification is not signed, so the charge is queried on the
            # PSP instead of being trusted as is.
            tx_sudo._bacenpix_poll_charge()
        return {}

    @staticmethod
    def _bacenpix_get_transaction(reference, access_token):
        """Return the transaction matching the reference and the access token.

        :param str reference: The reference of the transaction.
        :param str access_token: The access token used to verify the values.
        :return: The transaction.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If the access token is invalid or no transaction
                                matches the reference.
        """
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference)], limit=1)
        )
        if not tx_sudo:
            raise ValidationError(
                _("Pix: No transaction found matching reference %s.", reference)
            )
        if not payment_utils.check_access_token(
            access_token, reference, tx_sudo.partner_id.id
        ):
            raise ValidationError(_("Pix: Received tampered payment request data."))
        return tx_sudo
