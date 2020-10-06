# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint
import requests

from odoo import api, fields, models

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

    cielo_token = fields.Char(
        string="Token",
        required=False,
        )

    def _cielo_tokenize(self, values):
        aquirer_id = self.env.ref('payment_cielo.payment_acquirer_cielo')
        api_url_create_card = 'https://%s/1/card' % (
            aquirer_id._get_cielo_api_url())

        partner_id = self.env['res.partner'].browse(values['partner_id'])
        cielo_expiry = str(values['cc_expiry'][:2]) + '/20' + str(
            values['cc_expiry'][-2:])

        if values['cc_brand'] == 'mastercard':
            values['cc_brand'] = 'master'

        tokenize_params = {
            "CustomerName": partner_id.name,
            "CardNumber": values['cc_number'].replace(' ', ''),
            "Holder": values['cc_holder_name'],
            "ExpirationDate": cielo_expiry,
            "Brand": values['cc_brand'],
            }

        _logger.info(
            '_cielo_tokenize: Sending values to URL %s, values:\n%s',
            api_url_create_card, pprint.pformat(tokenize_params))
        r = requests.post(api_url_create_card,
                          json=tokenize_params,
                          headers=aquirer_id._get_cielo_api_headers())
        # TODO: Salvar token
        res = r.json()
        _logger.info('_create_cielo_charge: Values received:\n%s',
                     pprint.pformat(res))

        return res

    @api.model
    def cielo_create(self, values):
        token = values.get('cielo_token')

        token = self._cielo_tokenize(values)
        values['card_token'] = token['CardToken']
        description = None
        # payment_acquirer = self.env['payment.acquirer'].browse(
        #     values.get('acquirer_id'))

        if values.get('cc_number'):
            # payment_params = {
            #     'card[number]': values['cc_number'].replace(' ', ''),
            #     'card[exp_month]': str(values['cc_expiry'][:2]),
            #     'card[exp_year]': str(values['cc_expiry'][-2:]),
            #     'card[cvc]': values['cvc'],
            #     'card[name]': values['cc_holder_name'],
            # }
            description = values['cc_holder_name']
        else:
            partner_id = self.env['res.partner'].browse(values['partner_id'])
            description = 'Partner: %s (id: %s)' % (
                partner_id.name, partner_id.id)
        partner_id = self.env['res.partner'].browse(values['partner_id'])

        # res = self._cielo_create_customer(token, description,
        # payment_acquirer.id)

        customer_params = {
            # 'source': token['id'],
            'description': description or token["card"]["name"]
            }

        res = {
            'acquirer_ref': partner_id.id,
            'name': 'XXXXXXXXXXXX%s - %s' % (
                values['cc_number'][-4:], customer_params["description"]),
            'card_number': values['cc_number'].replace(' ', ''),
            'card_exp': str(values['cc_expiry'][:2]) + '/20' + str(
                values['cc_expiry'][-2:]),
            'card_cvc': values['cvc'],
            'card_holder': values['cc_holder_name'],
            'card_brand': values['cc_brand'],
            'cielo_token': values['card_token'],
            }

        # pop credit card info to info sent to create
        for field_name in ["card_number", "card_cvc", "card_holder",
        "card_exp"]:
            res.pop(field_name, None)
        return res

    # CURRENTLY UNUSED
    # def _cielo_create_customer(self, token, description=None,
    # acquirer_id=None):
    #     # if token.get('error'):
    #     #     _logger.error('payment.token.cielo_create_customer: Token
    #     error:\n%s', pprint.pformat(token['error']))
    #     #     raise Exception(token['error']['message'])
    #     #
    #     # if token['object'] != 'token':
    #     #     _logger.error('payment.token.cielo_create_customer: Cannot
    #     create a customer for object type "%s"', token.get('object'))
    #     #     raise Exception('We are unable to process your credit card
    #     information.')
    #     #
    #     # if token['type'] != 'card':
    #     #     _logger.error('payment.token.cielo_create_customer: Cannot
    #     create a customer for token type "%s"', token.get('type'))
    #     #     raise Exception('We are unable to process your credit card
    #     information.')
    #
    #     payment_acquirer = self.env['payment.acquirer'].browse(acquirer_id
    #     or self.acquirer_id.id)
    #     # url_customer = 'https://%s/customers' %
    #     payment_acquirer._get_cielo_api_url()
    #
    #     customer_params = {
    #         # 'source': token['id'],
    #         'description': description or token["card"]["name"]
    #     }
    #
    #     customer = r.json()
    #
    #     # if customer.get('error'):
    #     #     _logger.error('payment.token.cielo_create_customer: Customer
    #     error:\n%s', pprint.pformat(customer['error']))
    #     #     raise Exception(customer['error']['message'])
    #     #
    #     values = {
    #         'acquirer_ref': customer['id'],
    #         'name': 'XXXXXXXXXXXX%s - %s' % (token['card']['last4'],
    #         customer_params["description"])
    #     }
    #
    #     return True
