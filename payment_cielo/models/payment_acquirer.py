# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirerCielo(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cielo', 'Cielo')])
    cielo_merchant_key = fields.Char(required_if_provider='cielo',
                                     groups='base.group_user')
    cielo_merchant_id = fields.Char(string='Cielo Merchant Id',
                                    required_if_provider='cielo',
                                    groups='base.group_user')
    cielo_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user')

    @api.multi
    def cielo_s2s_form_validate(self, data):
        """Validates user input"""
        self.ensure_one()
        # mandatory fields
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry",
                           "cc_brand"]:
            if not data.get(field_name):
                return False
        return True

    @api.model
    def cielo_s2s_form_process(self, data):
        """Saves the payment.token object with data from cielo server

        Secret card info should be empty by this point.

        """
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

    @api.model
    def _get_cielo_api_url(self):
        """Get cielo API URLs used in all s2s communication

        Takes environment in consideration.

        """
        if self.environment == 'test':
            return 'apisandbox.cieloecommerce.cielo.com.br'
        if self.environment == 'prod':
            return 'api.cieloecommerce.cielo.com.br'

    @api.multi
    def _get_cielo_api_headers(self):
        """Get cielo API headers used in all s2s communication

        Takes environment in consideration. If environment is production
        merchant_id and merchant_key need to be defined.

        """
        if self.environment == 'test':
            CIELO_HEADERS = {
                'MerchantId': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
                'MerchantKey': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
                'Content-Type': 'application/json',
                }
        if self.environment == 'prod':
            CIELO_HEADERS = {
                'MerchantId': self.cielo_merchant_id,
                'MerchantKey': self.cielo_merchant_key,
                'Content-Type': 'application/json',
                }
        return CIELO_HEADERS

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerCielo, self)._get_feature_support()
        res['tokenize'].append('cielo')
        res['authorize'].append('cielo')
        return res
