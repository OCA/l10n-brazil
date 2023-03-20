# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests
from werkzeug.urls import url_join

from odoo import fields, models

PAY24PIX_PROVIDER = "pay24pix"


SANDBOX_URL = "https://sandbox.pay42.com.br/"
PROD_URL = "https://api.pay42.com.br/"

PIX_ENDPOINT_V2 = "v2/pix"
TRANSACTION_STATUS_V2 = "v2/transactions/?id={}"

PAY24PIX = {
    "enabled": PROD_URL,
    "test": SANDBOX_URL,
}


class PaymentAcquirer(models.Model):

    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[(PAY24PIX_PROVIDER, "Pay24 (pix)")],
        ondelete={PAY24PIX_PROVIDER: "set default"},
    )

    pay24pix_email_account = fields.Char("Email", groups="base.group_user")
    pay24pix_api_key = fields.Char(string="API KEY", groups="base.group_user")

    def pay24pix_compute_fees(self, amount, currency_id, country_id):
        """Compute fees

        :param float amount: the amount to pay
        :param integer country_id: an ID of a res.country, or None. This is
                                   the customer's country, to be compared to
                                   the acquirer company country.
        :return float fees: computed fees
        """
        fees = 0.0
        if self.fees_active:
            country = self.env["res.country"].browse(country_id)
            if country and self.company_id.sudo().country_id.id == country.id:
                percentage = self.fees_dom_var
                fixed = self.fees_dom_fixed
            else:
                percentage = self.fees_int_var
                fixed = self.fees_int_fixed
            fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        return fees

    def _pay24pix_header(self):
        return {
            "Authorization": self.pay24pix_api_key,
            "Content-Type": "application/json",
        }

    def _pay24pix_new_transaction(self, payload):
        response = requests.request(
            "POST",
            url_join(PAY24PIX[self.state], PIX_ENDPOINT_V2),
            headers=self._pay24pix_header(),
            data=payload,
        )
        return response

    def _pay24pix_status_transaction(self, tx_pay24_id):
        response = requests.request(
            "GET",
            url_join(PAY24PIX[self.state], TRANSACTION_STATUS_V2.format(tx_pay24_id)),
            headers=self._pay24pix_header(),
            data={},
        )
        return response

    def pay24pix_get_form_action_url(self):
        # 3. URL callback de feedback
        return "/payment/pay24pix/feedback"

    def _handle_pay24pix_webhook(self, tx_reference, jsonrequest):
        """Webhook para processamento da transação"""
        transaction_id = self.env["payment.transaction"].search(
            [
                ("callback_hash", "=", tx_reference),
                ("acquirer_id.provider", "=", PAY24PIX_PROVIDER),
            ]
        )
        if not transaction_id:
            return False
        return transaction_id._pay24pix_validate_webhook(tx_reference, jsonrequest)
