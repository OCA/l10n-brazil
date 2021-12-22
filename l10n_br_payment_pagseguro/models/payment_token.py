# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import datetime
import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTokenPagSeguro(models.Model):
    _inherit = 'payment.token'
    
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

    pagseguro_card_token = fields.Char(
        string="Token",
        required=False,
        )
        
    pagseguro_public_key = fields.Char(
        string='Public Key',
        required=False,
        )
    
    @api.model
    def pagseguro_create(self, values):
        """Treats tokenizing data.

         Calls _pagseguro_tokenize, formats the response data to the result and
         removes secret credit card information since it's now stored by pagseguro.
         A resulting dict containing card brand, card token, formated name (
         XXXXXXXXXXXX1234 - Customer Name) and partner_id will be returned.

        """
        if values.get('cc_number'):
            description = values['cc_holder_name']
        else:
            partner_id = self.env['res.partner'].browse(values['partner_id'])
            description = 'Partner: %s (id: %s)' % (
                partner_id.name, partner_id.id)
        partner_id = self.env['res.partner'].browse(values['partner_id'])

        customer_params = {
            'description': description
        }

        res = {
            'acquirer_ref': partner_id.id,
            'name': 'XXXXXXXXXXXX%s - %s' % (
                values['cc_number'][-4:], customer_params["description"]),
            'card_number': values['cc_number'].replace(' ', ''),
            'card_exp': str(values['cc_expiry'][:2]) + '/' + str(
                datetime.datetime.now().year)[:2] + str(
                values['cc_expiry'][-2:]),
            'card_cvc': values['cc_cvc'],
            'card_holder': values['cc_holder_name'],
            'card_brand': values['cc_brand'],
            'pagseguro_card_token': values['pagseguro_card_token'],
        }

        return res
