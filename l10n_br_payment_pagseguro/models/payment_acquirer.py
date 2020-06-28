# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('pagseguro', 'Pagseguro')])
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
