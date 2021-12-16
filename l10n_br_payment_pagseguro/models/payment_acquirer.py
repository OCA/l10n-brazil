# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class PaymentAcquirerPagseguro(models.Model):

    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('pagseguro', 'Pagseguro')])
    pagseguro_email = fields.Char(
        string='Email Client',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_token = fields.Char(
        string='Token',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    
    pagseguro_app_id = fields.Char(
        string='AppID',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_app_key = fields.Char(
        string='App Key',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_seller_mail = fields.Char(
        string='Seller Email',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_seller_password = fields.Char(
        string='Seller password',
        required_if_provider='pagseguro',
        groups='base.group_user'
    )
    pagseguro_seller_public_key = fields.Char(
        string='Seller Public Key',
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
