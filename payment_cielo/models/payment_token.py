# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import requests
import pprint

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

class PaymentTokenCielo(models.Model):
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


    @api.model
    def cielo_create(self, values):
        token = values.get('cielo_token')
        description = None
        payment_acquirer = self.env['payment.acquirer'].browse(values.get('acquirer_id'))
        # when asking to create a token on Stripe servers
        if values.get('cc_number'):
            payment_params = {
                'card[number]': values['cc_number'].replace(' ', ''),
                'card[exp_month]': str(values['cc_expiry'][:2]),
                'card[exp_year]': str(values['cc_expiry'][-2:]),
                'card[cvc]': values['cvc'],
                'card[name]': values['cc_holder_name'],
            }
            description = values['cc_holder_name']
        else:
            partner_id = self.env['res.partner'].browse(values['partner_id'])
            description = 'Partner: %s (id: %s)' % (partner_id.name, partner_id.id)
        partner_id = self.env['res.partner'].browse(values['partner_id'])

        # res = self._cielo_create_customer(token, description, payment_acquirer.id)

        customer_params = {
            # 'source': token['id'],
            'description': description or token["card"]["name"]
        }

        res = {
            'acquirer_ref': partner_id.id,
            'name': 'XXXXXXXXXXXX%s - %s' % (values['cc_number'][-4:], customer_params["description"]),
            'card_number': values['cc_number'].replace(' ', ''),
            'card_exp': str(values['cc_expiry'][:2]) + '/20' + str(values['cc_expiry'][-2:]),
            'card_cvc': values['cvc'],
            'card_holder': values['cc_holder_name'],
            'card_brand': values['cc_brand'],
        }

        # pop credit card info to info sent to create
        # for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand", "cielo_token"]:
        #     values.pop(field_name, None)
        return res


    def _cielo_create_customer(self, token, description=None, acquirer_id=None):
        # if token.get('error'):
        #     _logger.error('payment.token.cielo_create_customer: Token error:\n%s', pprint.pformat(token['error']))
        #     raise Exception(token['error']['message'])
        #
        # if token['object'] != 'token':
        #     _logger.error('payment.token.cielo_create_customer: Cannot create a customer for object type "%s"', token.get('object'))
        #     raise Exception('We are unable to process your credit card information.')
        #
        # if token['type'] != 'card':
        #     _logger.error('payment.token.cielo_create_customer: Cannot create a customer for token type "%s"', token.get('type'))
        #     raise Exception('We are unable to process your credit card information.')

        payment_acquirer = self.env['payment.acquirer'].browse(acquirer_id or self.acquirer_id.id)
        # url_customer = 'https://%s/customers' % payment_acquirer._get_cielo_api_url()

        customer_params = {
            # 'source': token['id'],
            'description': description or token["card"]["name"]
        }

        customer = r.json()

        # if customer.get('error'):
        #     _logger.error('payment.token.cielo_create_customer: Customer error:\n%s', pprint.pformat(customer['error']))
        #     raise Exception(customer['error']['message'])
        #
        values = {
            'acquirer_ref': customer['id'],
            'name': 'XXXXXXXXXXXX%s - %s' % (token['card']['last4'], customer_params["description"])
        }

        return True
