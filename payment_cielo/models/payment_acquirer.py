# coding: utf-8

import logging
import requests
import pprint

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class PaymentAcquirerCielo(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cielo', 'Cielo')])
    cielo_secret_key = fields.Char(required_if_provider='cielo', groups='base.group_user')
    cielo_publishable_key = fields.Char(required_if_provider='cielo', groups='base.group_user')
    cielo_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user')

    @api.multi
    def cielo_s2s_form_validate(self, data):
        self.ensure_one()

        # mandatory fields
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand"]:
            if not data.get(field_name):
                return False
        return True

    @api.model
    def cielo_s2s_form_process(self, data):
        payment_token = self.env['payment.token'].sudo().create({
            'cc_number': data['cc_number'],
            'cc_holder_name': data['cc_holder_name'],
            'cc_expiry': data['cc_expiry'],
            'cc_brand': data['cc_brand'],
            'cvc': data['cvc'],
            'acquirer_id': int(data['acquirer_id']),
            'partner_id': int(data['partner_id']),
        })
        return payment_token
        # return True

    @api.model
    def _get_cielo_api_url(self):
        if self.environment == 'test':
            return 'apisandbox.cieloecommerce.cielo.com.br'
        if self.environment == 'prod':
            return 'api.cieloecommerce.cielo.com.br'

