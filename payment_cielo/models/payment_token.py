# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTokenCielo(models.Model):
    _inherit = "payment.token"

    card_number = fields.Char(
        string="Number",
        required=False,
    )

    card_holder = fields.Char(
        string="Holder",
        required=False,
    )

    card_exp = fields.Char(
        string="Expiration date",
        required=False,
    )

    card_cvc = fields.Char(
        string="cvc",
        required=False,
    )

    card_brand = fields.Char(
        string="Brand",
        required=False,
    )

    cielo_token = fields.Char(
        string="Token",
        required=False,
    )

    def _cielo_tokenize(self, values):
        """Tokenize card in Cielo server.

        Send card data to Cielo and get back a token. Return the response
        dict, which still contains all credit card data.
        """
        aquirer_id = self.env.ref("payment_cielo.payment_acquirer_cielo")
        api_url_create_card = "https://%s/1/card" % (aquirer_id._get_cielo_api_url())

        partner_id = self.env["res.partner"].browse(values["partner_id"])
        cielo_expiry = (
            str(values["cc_expiry"][:2])
            + "/"
            + str(datetime.datetime.now().year)[:2]
            + str(values["cc_expiry"][-2:])
        )

        if values["cc_brand"] == "mastercard":
            values["cc_brand"] = "master"

        tokenize_params = {
            "CustomerName": partner_id.name,
            "CardNumber": values["cc_number"].replace(" ", ""),
            "Holder": values["cc_holder_name"],
            "ExpirationDate": cielo_expiry,
            "Brand": values["cc_brand"],
        }

        _logger.info("_cielo_tokenize: Sending values to URL %s", api_url_create_card)
        r = requests.post(
            api_url_create_card,
            json=tokenize_params,
            headers=aquirer_id._get_cielo_api_headers(),
        )
        res = r.json()
        return res

    @api.model
    def cielo_create(self, values):
        """Treat tokenizing data.

        Call _cielo_tokenize, format the response data to the result and
        remove secret credit card information since it's now stored by Cielo.
        Return a resulting dict containing card brand, card token, formatted
        name (XXXXXXXXXXXX1234 - Customer Name), and partner_id.
        """
        token = self._cielo_tokenize(values)
        if "CardToken" not in token:
            return False
        values["card_token"] = token["CardToken"]

        if values.get("cc_number"):
            description = values["cc_holder_name"]
        else:
            partner_id = self.env["res.partner"].browse(values["partner_id"])
            description = "Partner: %s (id: %s)" % (partner_id.name, partner_id.id)
        partner_id = self.env["res.partner"].browse(values["partner_id"])

        customer_params = {"description": description or token["card"]["name"]}

        res = {
            "acquirer_ref": partner_id.id,
            "name": "XXXXXXXXXXXX%s - %s"
            % (values["cc_number"][-4:], customer_params["description"]),
            "card_number": values["cc_number"].replace(" ", ""),
            "card_exp": str(values["cc_expiry"][:2])
            + "/"
            + str(datetime.datetime.now().year)[:2]
            + str(values["cc_expiry"][-2:]),
            "card_cvc": values["cvc"],
            "card_holder": values["cc_holder_name"],
            "card_brand": values["cc_brand"],
            "cielo_token": values["card_token"],
        }

        # Pop credit card info from info sent to create
        for field_name in ["card_number", "card_cvc", "card_holder", "card_exp"]:
            res.pop(field_name, None)
        return res
