# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class PaymentAcquirerPagseguro(models.Model):

    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('pagseguro', 'Pagseguro')])    
    
    pagseguro_email = fields.Char(
        string='Email',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_token = fields.Char(
        string='Token',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    
    @api.model
    def _get_pagseguro_api_url(self):
        """Get pagseguro API URLs used in all s2s communication

        Takes environment in consideration.

        """
        if self.environment == 'test':
            return 'sandbox.api.pagseguro.com'
        if self.environment == 'prod':
            return 'api.pagseguro.com'

    @api.multi
    def pagseguro_s2s_form_validate(self, data):
        """Validates user input"""
        self.ensure_one()
        # mandatory fields
        for field_name in ["cc_number", "cc_cvc", "cc_holder_name", "cc_expiry",
                           "cc_brand"]:
            if not data.get(field_name):
                return False
        return True

    @api.model
    def pagseguro_s2s_form_process(self, data):
        """Saves the payment.token object with data from PagSeguro server

        Secret card info should be empty by this point.

        """
        payment_token = self.env['payment.token'].sudo().create({
            'cc_number': data['cc_number'],
            'cc_holder_name': data['cc_holder_name'],
            'cc_expiry': data['cc_expiry'],
            'cc_brand': data['cc_brand'],
            'cc_cvc': data['cc_cvc'],
            'acquirer_ref': int(data['partner_id']),
            'acquirer_id': int(data['acquirer_id']),
            'partner_id': int(data['partner_id']),
        })
        return payment_token

    @api.model
    def _get_pagseguro_api_url(self):
        """Get pagseguro API URLs used in all s2s communication

        Takes environment in consideration.

        """
        if self.environment == 'test':
            return 'sandbox.api.pagseguro.com'
        if self.environment == 'prod':
            return 'api.pagseguro.com'

    @api.multi
    def _get_pagseguro_api_headers(self):
        """Get pagseguro API headers used in all s2s communication

        Takes app key in consideration.

        """
        PAGSEGURO_HEADERS = {
            'Authorization': f'Bearer {self.pagseguro_app_key}',
            'Content-Type': 'application/json',
        }

        return PAGSEGURO_HEADERS

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
        res = super()._get_feature_support()
        res['authorize'].append('pagseguro')
        res['tokenize'].append('pagseguro')
        return res
