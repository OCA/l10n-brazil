# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint
import requests
import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTokenPagseguro(models.Model):
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

    pagseguro_token = fields.Char(
        string="Token",
        required=False,
        )

    def _pagseguro_tokenize(self, values):
        """Tokenize card in pagseguro server.

        Sends card data to pagseguro and gets back a token. Returns the response
        dict which still contains all credit card data.
        """
        aquirer_id = self.env.ref('l10n_br_payment_pagseguro.payment_acquirer_pagseguro')
        api_url_create_card = 'https://%s/1/card' % ( # TODO Search create card endpoint
            aquirer_id._get_pagseguro_api_url())

        partner_id = self.env['res.partner'].browse(values['partner_id'])
        pagseguro_expiry = str(values['cc_expiry'][:2]) + '/' + str(
            datetime.datetime.now().year)[:2] + str(values['cc_expiry'][-2:])

        if values['cc_brand'] == 'mastercard':
            values['cc_brand'] = 'master'

        tokenize_params = {
            "CustomerName": partner_id.name,
            "CardNumber": values['cc_number'].replace(' ', ''),
            "Holder": values['cc_holder_name'],
            "ExpirationDate": pagseguro_expiry,
            "Brand": values['cc_brand'],
            }

        _logger.info("_cielo_tokenize: Sending values to URL %s", api_url_create_card)
        r = requests.post(api_url_create_card,
                          json=tokenize_params,
                      s    headers=aquirer_id._get_pagseguro_api_headers())
        res = r.json()
        _logger.info('_create_cielo_charge: Values received:\n%s',
                     pprint.pformat(res))

        return res
