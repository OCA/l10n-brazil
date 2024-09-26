# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransactionPagseguro(models.Model):
    _inherit = "payment.transaction"

    pagseguro_s2s_capture_link = fields.Char(
        string="Capture Link Pagseguro",
        required=False,
    )
    pagseguro_s2s_void_link = fields.Char(
        string="Cancel Link",
        required=False,
    )
    pagseguro_s2s_check_link = fields.Char(
        string="Check Link Pagseguro",
        required=False,
    )

    def _create_pagseguro_charge(self):
        """Creates the s2s payment.

        Uses encrypted credit card.
        """
        api_url_charge = "https://%s/charges" % (
            self.acquirer_id._get_pagseguro_api_url()
        )

        self.payment_token_id.active = False

        _logger.info(
            "_create_pagseguro_charge: Sending values to URL %s", api_url_charge
        )
        r = requests.post(
            api_url_charge,
            json=self._get_pagseguro_charge_params(),
            headers=self.acquirer_id._get_pagseguro_api_headers(),
        )
        res = r.json()
        _logger.info(
            "_create_pagseguro_charge: Values received:\n%s",
            self.pprint_filtered_response(res),
        )
        return res

    def pagseguro_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        result = self._create_pagseguro_charge()

        return self._pagseguro_s2s_validate_tree(result)

    def pagseguro_s2s_capture_transaction(self):
        """Captures an authorized transaction."""
        currencies = self.sale_order_ids.currency_id.mapped(
            "name"
        )  # Add all sale orders currencies
        currencies += self.invoice_ids.currency_id.mapped(
            "name"
        )  # Add all invoices currencies
        if any([currency != "BRL" for currency in currencies]):
            raise ValidationError(
                _(
                    "Please check if all related sale orders and invoices are in BRL "
                    "currency (supported by pagseguro)."
                )
            )

        _logger.info(
            "pagseguro_s2s_capture_transaction: Sending values to URL %s",
            self.pagseguro_s2s_capture_link,
        )
        r = requests.post(
            self.pagseguro_s2s_capture_link,
            headers=self.acquirer_id._get_pagseguro_api_headers(),
            json=self._get_pagseguro_charge_params(),
        )
        res = r.json()
        _logger.info(
            "pagseguro_s2s_capture_transaction: Values received:\n%s",
            self.pprint_filtered_response(res),
        )

        if (
            isinstance(res, dict)
            and res.get("payment_response")
            and res.get("payment_response").get("message") == "SUCESSO"
        ):
            # apply result
            self.log_transaction(res["id"], res["payment_response"]["message"])
            self._set_transaction_done()
            self.execute_callback()
        else:
            self.log_transaction(
                reference=res["error_messages"][0]["code"],
                message=res["error_messages"][0]["message"],
            )

    def pagseguro_s2s_void_transaction(self):
        """Voids an authorized transaction."""
        _logger.info(
            "pagseguro_s2s_void_transaction: Sending values to URL %s",
            self.pagseguro_s2s_void_link,
        )
        headers = {
            "Authorization": self.acquirer_id.pagseguro_token,
            "x-api-version": "4.0",
        }

        params = {
            "charge_id": self.id,
            "amount": {
                "value": int(self.amount * 100),
            },
        }

        r = requests.post(
            self.pagseguro_s2s_void_link,
            headers=headers,
            json=params,
        )
        res = r.json()
        _logger.info(
            "pagseguro_s2s_void_transaction: Values received:\n%s",
            self.pprint_filtered_response(res),
        )

        if (
            isinstance(res, dict)
            and res.get("payment_response")
            and res.get("payment_response").get("message") == "SUCESSO"
        ):
            # apply result
            self.log_transaction(res["id"], res["payment_response"]["message"])
            self._set_transaction_cancel()
        else:
            self.log_transaction(
                reference=res["error_messages"][0]["code"],
                message=res["error_messages"][0]["message"],
            )

    def _pagseguro_s2s_validate_tree(self, tree):
        """Validates the transaction.

        This method updates the payment.transaction object describing the
        actual transaction outcome.
        Also saves get/capture/void links sent by pagseguro to make it easier to
        perform the operations.

        """
        self.ensure_one()
        if self.state != "draft":
            _logger.info(
                "PagSeguro: trying to validate an already validated tx (ref %s)",
                self.reference,
            )
            return True

        if tree.get("payment_response"):
            code = tree.get("payment_response", {}).get("code")
            if code == "20000":
                self.log_transaction(reference=tree.get("id"), message="")

            # store capture and void links for future manual operations
            for method in tree.get("links"):
                if "rel" in method and "href" in method:
                    if method.get("rel") == "SELF":
                        self.pagseguro_s2s_check_link = method.get("href")
                    if method.get("rel") == "CHARGE.CAPTURE":
                        self.pagseguro_s2s_capture_link = method.get("href")
                    if method.get("rel") == "CHARGE.CANCEL":
                        self.pagseguro_s2s_void_link = method.get("href")

            # setting transaction to authorized - must match Pagseguro
            # payment using the case without automatic capture
            self._set_transaction_authorized()
            self.execute_callback()
            if self.payment_token_id:
                self.payment_token_id.verified = True
                return True
            else:
                self._validate_tree_message(tree)
                return False

        self._validate_tree_message(tree)

        return False

    def _validate_tree_message(self, tree):
        if tree.get("message"):
            error = tree.get("message")
            _logger.warning(error)
            self.sudo().write(
                {
                    "state_message": error,
                    "acquirer_reference": tree.get("id"),
                    "date": fields.datetime.now(),
                }
            )
            self._set_transaction_cancel()

    def _get_pagseguro_charge_params(self):
        """
        Returns dict containing the required body information to create a
        charge on Pagseguro.

        Uses the payment amount, currency and encrypted credit card.

        Returns:
            dict: Charge parameters
        """
        # currency = self.acquirer_id.company_id.currency_id.name
        # if currency != "BRL":
        #     raise UserError(_("Only BRL currency is allowed."))
        CHARGE_PARAMS = {
            "reference_id": str(self.payment_token_id.acquirer_id.id),
            "description": self.display_name[:13],
            "amount": {
                # Charge is in BRL cents -> Multiply by 100
                "value": int(self.amount * 100),
                "currency": "BRL",
            },
            "payment_method": {
                "soft_descriptor": self.acquirer_id.company_id.name,
                "type": "CREDIT_CARD",
                "installments": 1,
                "capture": False,
                "card": {
                    "encrypted": self.payment_token_id.pagseguro_card_token,
                },
            },
        }

        return CHARGE_PARAMS

    def log_transaction(self, reference, message):
        """Logs a transaction. It can be either a successful or a failed one."""
        self.sudo().write(
            {
                "date": fields.datetime.now(),
                "acquirer_reference": reference,
                "state_message": message,
            }
        )

    @staticmethod
    def pprint_filtered_response(response):
        # Returns response removing payment's sensitive information
        output_response = response.copy()
        output_response.pop("links", None)
        output_response.pop("metadata", None)
        output_response.pop("notification_urls", None)
        output_response.pop("payment_method", None)

        return pprint.pformat(output_response)
