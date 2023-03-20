# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import hmac
import json
import logging
from datetime import datetime

from werkzeug.urls import url_join

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import consteq, ustr

_logger = logging.getLogger(__name__)


PAY24PIX_STATUS_CREATED = 0
PAY24PIX_STATUS_PAID = 1
PAY24PIX_STATUS_REJECTED = 2
PAY24PIX_STATUS_EXPIRED = 3
PAY24PIX_STATUS_REFUNDED = 4


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    pay24pix_date_due = fields.Datetime()
    pay24pix_qrcode = fields.Char()
    pay24pix_currency = fields.Char()
    pay24pix_amount = fields.Float()

    def _get_processing_info(self):
        # Devolver Dados do QRCODE
        res = super()._get_processing_info()
        if self.acquirer_id.provider == "pay24pix":
            if self.state == "draft":
                vals = {
                    "message_to_display": """
                        <span>
                            <h6> PIX: {} </h6>
                            <img src="/report/barcode/QR/{}?width=200&amp;height=200"/>
                            </br>
                            <div class="badge pull-right">
                                <h5>{} {}</h5>
                            </div>
                        </span>
                        """.format(
                        self.pay24pix_qrcode,
                        self.pay24pix_qrcode,
                        self.amount,
                        self.currency_id.name,
                    ),
                }
                res.update(vals)
            if self.state == "pending":
                vals = {
                    "message_to_display": """
                        <h5> <bold> Confirmações Pendentes 1 de 3 </bold></h5>
                    """,
                }
                res.update(vals)
        return res

    def action_pay24pix_check_transaction_status(self):
        for record in self:
            record._pay24pix_check_transaction_status()

    def _pay24pix_check_transaction_status(self, post=None):
        if post:
            _logger.info(post)

        response = self.acquirer_id._pay24pix_status_transaction(
            self.acquirer_reference
        )
        response_data = response.json()

        if response_data.get("status") == PAY24PIX_STATUS_CREATED:
            _logger.info("PAY24PIX_STATUS_CREATED")
            self._set_transaction_pending()
        elif response_data.get("status") == PAY24PIX_STATUS_PAID:
            _logger.info("PAY24PIX_STATUS_PAID")
            self._set_transaction_done()
            self._post_process_after_done()
        elif response_data.get("status") == PAY24PIX_STATUS_REJECTED:
            _logger.info("PAY24PIX_STATUS_REJECTED")
            self._set_transaction_error()
        elif response_data.get("status") == PAY24PIX_STATUS_EXPIRED:
            _logger.info("PAY24PIX_STATUS_EXPIRED")
            self._set_transaction_cancel()
            self.invoice_ids.button_draft()
            self.invoice_ids.button_cancel()
        elif response_data.get("status") == PAY24PIX_STATUS_REFUNDED:
            _logger.info("PAY24PIX_STATUS_REFUNDED")

    def _pay24pix_validate_webhook(self, valid_token, post):
        callback_hash = self._pay24pix_generate_callback_hash(self.reference)
        if not consteq(ustr(valid_token), callback_hash):
            _logger.warning("Invalid callback signature for transaction %d" % (self.id))
            return False
        _logger.info("Invalid callback signature for transaction %d" % (self.id))
        return self._pay24pix_check_transaction_status(post)

    def _pay24pix_generate_callback_hash(self, reference):
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")
        return hmac.new(
            secret.encode("utf-8"), reference.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def pay24pix_create(self, values):
        """Compleate the values used to create the payment.transaction"""

        partner_id = self.env["res.partner"].browse(values.get("partner_id", []))
        self.env["res.currency"].browse(values.get("currency_id", []))
        acquirer_id = self.env["payment.acquirer"].browse(values.get("acquirer_id", []))

        invoice_due_dates = (
            self.env["account.move"]
            .browse([x[2][0] for x in values.get("invoice_ids")])
            .filtered("invoice_date_due")
            .mapped("invoice_date_due")
        )
        if invoice_due_dates:
            due = max(invoice_due_dates)
        else:
            due = fields.Date.context_today(self)
        due = datetime.combine(due, datetime.max.time())

        base_url = acquirer_id.get_base_url()
        # base_url = "https://.....sa.ngrok.io"

        callback_hash = self._pay24pix_generate_callback_hash(values.get("reference"))

        webhook = url_join(
            base_url, "/payment/pay24pix/webhook/{}".format(callback_hash)
        )
        _logger.info(webhook)

        payload = json.dumps(
            {
                "transaction_id": values.get("reference"),
                # "currency": currency_id.name,
                "currency": "BRL",
                "amount": values.get("amount"),
                "due": due.strftime("%Y-%m-%dT%H:%M:%S"),
                "name": values.get("partner_name"),
                "document_type": "CPF",
                "document_number": partner_id.vat,
                "webhook": webhook,
            }
        )
        response = acquirer_id._pay24pix_new_transaction(payload)
        response_data = response.json()
        if not response.ok:
            raise ValidationError(
                _("Payload Error {type} \n {message}".format(**response_data))
            )
        else:
            _logger.info(response_data)
            return dict(
                acquirer_reference=response_data.get("id"),
                state_message=response_data.get("status"),
                callback_hash=callback_hash,
                # pay24pix_currency=response_data.get('currency'),
                # pay24pix_amount=response_data.get('amount'),
                pay24pix_date_due=due,
                pay24pix_qrcode=response_data.get("qrcode"),
                date=datetime.now(),
            )
