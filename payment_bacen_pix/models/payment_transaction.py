# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint
import re
import uuid
from datetime import datetime, timedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils

from ..const import DEFAULT_EXPIRATION, PAYMENT_STATUS_MAPPING
from ..utils import redact_personal_data

_logger = logging.getLogger(__name__)

# The txid of a charge is limited to 26..35 alphanumeric characters by the Pix
# API, so the reference of the transaction cannot be used as is.
TXID_PATTERN = re.compile(r"^[a-zA-Z0-9]{26,35}$")


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    bacenpix_txid = fields.Char(
        string="Pix Transaction Id",
        help="The identifier of the charge on the Pix arrangement.",
        readonly=True,
    )
    bacenpix_qrcode = fields.Char(
        string="Pix Copy and Paste",
        help="The payload of the QR code, which the payer can also copy and "
        "paste in their banking application.",
        readonly=True,
    )
    bacenpix_location = fields.Char(
        string="Pix Location",
        help="The location of the payload registered with the PSP.",
        readonly=True,
    )
    bacenpix_expiration = fields.Datetime(
        string="Pix Expiration",
        help="The moment after which the charge can no longer be paid.",
        readonly=True,
    )

    # === BUSINESS METHODS === #

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return the values of the Pix charge.

        The charge is created on the PSP so that the payer already finds the QR
        code when the payment page opens.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values.
        :return: The provider-specific rendering values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "bacenpix":
            return res

        if not self.bacenpix_txid:
            self._bacenpix_create_charge()

        return {
            "api_url": "/payment/bacenpix/qrcode",
            "reference": self.reference,
            "access_token": payment_utils.generate_access_token(
                self.reference, self.partner_id.id
            ),
        }

    def _bacenpix_create_charge(self):
        """Create the immediate charge on the PSP and store its QR code.

        :return: None
        """
        self.ensure_one()

        txid = uuid.uuid4().hex
        payload = {
            "calendario": {
                "expiracao": self.provider_id.bacenpix_expiration or DEFAULT_EXPIRATION
            },
            "valor": {"original": f"{self.amount:.2f}"},
            "chave": self.provider_id.sudo().bacenpix_key,
            "solicitacaoPagador": self.reference[:140],
        }
        debtor = self._bacenpix_prepare_debtor_payload()
        if debtor:
            payload["devedor"] = debtor

        response_content = self.provider_id._bacenpix_make_request(
            f"/cob/{txid}", payload, method="PUT"
        )
        _logger.info(
            "charge creation response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(redact_personal_data(response_content)),
        )

        qr_code = response_content.get("pixCopiaECola")
        if not qr_code:
            raise ValidationError(
                _("Pix: The charge was created without a QR code payload.")
            )
        self.write(
            {
                "bacenpix_txid": response_content.get("txid") or txid,
                "bacenpix_qrcode": qr_code,
                "bacenpix_location": (response_content.get("loc") or {}).get("location")
                or response_content.get("location"),
                "bacenpix_expiration": self._bacenpix_compute_expiration(
                    response_content
                ),
            }
        )
        self._handle_notification_data("bacenpix", {"response": response_content})

    def _bacenpix_prepare_debtor_payload(self):
        """Return the `devedor` part of the payload of a charge.

        The Pix API only accepts a debtor with a valid CPF or CNPJ, so the
        section is left out when the partner has no tax id.

        :return: The debtor payload, or an empty dict.
        :rtype: dict
        """
        self.ensure_one()

        tax_id = re.sub(r"\D", "", self.partner_id.vat or "")
        name = (self.partner_name or self.partner_id.name or "")[:200]
        if not name:
            return {}
        if len(tax_id) == 11:
            return {"cpf": tax_id, "nome": name}
        elif len(tax_id) == 14:
            return {"cnpj": tax_id, "nome": name}
        return {}

    @staticmethod
    def _bacenpix_compute_expiration(response_content):
        """Return the moment the charge expires, out of its calendar.

        :param dict response_content: The charge as returned by the PSP.
        :return: The expiration of the charge.
        :rtype: datetime|bool
        """
        calendar = response_content.get("calendario") or {}
        creation = calendar.get("criacao")
        expiration = calendar.get("expiracao")
        if not creation or not expiration:
            return False
        try:
            created_at = datetime.fromisoformat(creation.replace("Z", "+00:00"))
            created_at = created_at.replace(tzinfo=None)
            return created_at + timedelta(seconds=int(expiration))
        except (ValueError, TypeError):
            return False

    def _bacenpix_poll_charge(self):
        """Query the charge on the PSP and process its status.

        :return: None
        """
        self.ensure_one()

        if not self.bacenpix_txid:
            return
        response_content = self.provider_id._bacenpix_make_request(
            f"/cob/{self.bacenpix_txid}", method="GET"
        )
        _logger.info(
            "charge query response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(redact_personal_data(response_content)),
        )
        self._handle_notification_data("bacenpix", {"response": response_content})

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on Pix data.

        :param str provider_code: The code of the provider that handled the tx.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If no transaction is found matching the data.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "bacenpix" or len(tx) == 1:
            return tx

        txid = (notification_data.get("response") or {}).get("txid")
        if not txid:
            raise ValidationError(_("Pix: Received data with missing txid."))
        tx = self.search(
            [("bacenpix_txid", "=", txid), ("provider_code", "=", "bacenpix")]
        )
        if not tx:
            raise ValidationError(
                _("Pix: No transaction found matching txid %s.", txid)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the transaction based on Pix data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "bacenpix":
            return

        response_content = notification_data.get("response") or {}
        status = response_content.get("status")
        if not status:
            raise ValidationError(_("Pix: Received data with missing status."))

        # The end to end id of the payment identifies it on the arrangement.
        payments = response_content.get("pix") or []
        if payments and payments[0].get("endToEndId"):
            self.provider_reference = payments[0]["endToEndId"]

        if status in PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
            if self.operation == "refund":
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        elif status in PAYMENT_STATUS_MAPPING["pending"]:
            if self.state != "pending":
                self._set_pending()
        elif status in PAYMENT_STATUS_MAPPING["cancel"]:
            self._set_canceled(state_message=status)
        else:
            _logger.warning(
                "received data with invalid status %(status)s for transaction "
                "with reference %(ref)s",
                {"status": status, "ref": self.reference},
            )
            self._set_error(_("Pix: Received data with invalid status: %s", status))

    def _cron_bacenpix_poll_pending_transactions(self):
        """Query the PSP for the charges that are still waiting for a payment.

        The webhook of the arrangement is the fastest way to be notified, but it
        requires the Odoo instance to be reachable by the PSP: this cron makes
        the module work without it.

        :return: None
        """
        pending_transactions = self.search(
            [
                ("provider_code", "=", "bacenpix"),
                ("state", "in", ("draft", "pending")),
                ("bacenpix_txid", "!=", False),
            ]
        )
        for transaction in pending_transactions:
            try:
                transaction._bacenpix_poll_charge()
            except ValidationError:
                _logger.warning(
                    "could not poll the charge of the transaction with reference %s",
                    transaction.reference,
                    exc_info=True,
                )
