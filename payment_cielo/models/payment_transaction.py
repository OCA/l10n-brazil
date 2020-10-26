# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import requests
import pprint

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# TODO: INT_CURRENCIES é necessário?
INT_CURRENCIES = [
    u'BRL', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA',
    u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
    ]


class PaymentTransactionCielo(models.Model):
    _inherit = 'payment.transaction'

    cielo_s2s_capture_link = fields.Char(
        string="Capture Link",
        required=False,
        )

    cielo_s2s_void_link = fields.Char(
        string="Void Link",
        required=False,
        )

    cielo_s2s_check_link = fields.Char(
        string="Check Link",
        required=False,
        )

    def _create_cielo_charge(self, acquirer_ref=None, tokenid=None,
                             email=None):
        api_url_charge = 'https://%s/1/sales' % (
            self.acquirer_id._get_cielo_api_url())

        if self.payment_token_id.card_brand == 'mastercard':
            self.payment_token_id.card_brand = 'master'

        # self.payment_token_id.cielo_token

        charge_params = {
            #  TODO: MerchantOrderId - Numero de identificação do Pedido.
            "MerchantOrderId": "2014111703",
            "Customer": {
                "Name": self.partner_id.name
                },
            "Payment": {
                "Type": "CreditCard",
                "Amount": self.amount * 100,
                "Installments": 1,
                # TODO: SoftDescriptor - Texto impresso na fatura bancaria
                #  comprador. Deve ser preenchido de acordo com os dados do
                #  sub Merchant.
                "SoftDescriptor": "123456789ABCD",
                "CreditCard": {
                    "CardToken": self.payment_token_id.cielo_token,
                    "Brand": self.payment_token_id.card_brand,
                    "SaveCard": "true"
                    }
                }
            }

        self.payment_token_id.active = False

        # charge_params = {
        #     'amount': int(self.amount if self.currency_id.name in
        #     INT_CURRENCIES else float_round(self.amount * 100, 2)),
        #     'currency': self.currency_id.name,
        #     'metadata[reference]': self.reference,
        #     'description': self.reference,
        # }
        # if acquirer_ref:
        #     charge_params['customer'] = acquirer_ref
        # if tokenid:
        #     charge_params['card'] = str(tokenid)
        # if email:
        #     charge_params['receipt_email'] = email.strip()

        _logger.info(
            '_create_cielo_charge: Sending values to URL %s, values:\n%s',
            api_url_charge, pprint.pformat(charge_params))
        r = requests.post(api_url_charge,
                          json=charge_params,
                          headers=self.acquirer_id._get_cielo_api_headers())
        res = r.json()
        _logger.info('_create_cielo_charge: Values received:\n%s',
                     pprint.pformat(res))
        return res

    @api.multi
    def cielo_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        result = self._create_cielo_charge(
            acquirer_ref=self.payment_token_id.acquirer_ref,
            email=self.partner_email)
        return self._cielo_s2s_validate_tree(result)

    @api.multi
    def cielo_s2s_capture_transaction(self):
        _logger.info(
            'cielo_s2s_capture_transaction: Sending values to URL %s',
            self.cielo_s2s_capture_link)
        r = requests.put(self.cielo_s2s_capture_link,
                         headers=self.acquirer_id._get_cielo_api_headers())
        res = r.json()
        _logger.info('cielo_s2s_capture_transaction: Values received:\n%s',
                     pprint.pformat(res))
        # analyse result
        if type(res) == dict and res.get('ProviderReturnMessage') and res.get(
                'ProviderReturnMessage') == 'Operation Successful':
            # apply result
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': res,
                })
            self._set_transaction_done()
            self.execute_callback()
        else:
            self.sudo().write({
                'state_message': res,
                'acquirer_reference': res,
                'date': fields.datetime.now(),
                })

    @api.multi
    def cielo_s2s_void_transaction(self):
        _logger.info(
            'cielo_s2s_void_transaction: Sending values to URL %s',
            self.cielo_s2s_void_link)
        r = requests.put(self.cielo_s2s_void_link,
                         headers=self.acquirer_id._get_cielo_api_headers())
        res = r.json()
        _logger.info('cielo_s2s_void_transaction: Values received:\n%s',
                     pprint.pformat(res))
        # analyse result
        if type(res) == dict and res.get('ProviderReturnMessage') and res.get(
                'ProviderReturnMessage') == 'Operation Successful':
            # apply result
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': res,
                })
            self._set_transaction_cancel()
        else:
            self.sudo().write({
                'state_message': res,
                'acquirer_reference': res,
                'date': fields.datetime.now(),
                })

    @api.multi
    def _cielo_s2s_validate_tree(self, tree):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info(
                'Cielo: trying to validate an already validated tx (ref %s)',
                self.reference)
            return True

        if type(tree) != list:
            status = tree.get('Payment').get('Status')
            if status == 1:
                self.write({
                    'date': fields.datetime.now(),
                    'acquirer_reference': tree.get('id'),
                    })
                # store capture and void links for future manual operations
                for method in tree.get('Payment').get('Links'):
                    if 'Rel' in method and 'Href' in method:
                        if method.get('Rel') == 'self':
                            self.cielo_s2s_check_link = method.get('Href')
                        if method.get('Rel') == 'capture':
                            self.cielo_s2s_capture_link = method.get('Href')
                        if method.get('Rel') == 'void':
                            self.cielo_s2s_void_link = method.get('Href')

                # setting transaction to authorized - must match Cielo
                # payment using the case without automatic capture
                self._set_transaction_authorized()
                self.execute_callback()
                if self.payment_token_id:
                    self.payment_token_id.verified = True
                return True
            else:
                error = tree.get('Payment').get('ReturnMessage')
                _logger.warn(error)
                self.sudo().write({
                    'state_message': error,
                    'acquirer_reference': tree.get('id'),
                    'date': fields.datetime.now(),
                    })
                self._set_transaction_cancel()
                return False

        elif type(tree) == list:
            error = tree[0].get('Message')
            _logger.warn(error)
            self.sudo().write({
                'state_message': error,
                'date': fields.datetime.now(),
                })
            self._set_transaction_cancel()
            return False
