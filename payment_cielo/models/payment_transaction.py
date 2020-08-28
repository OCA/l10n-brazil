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

# TODO: MerchantId e MerchantKey de hml e produção (pegar valor da produção das configurações do payent acquirer
CIELO_HEADERS = {
        'MerchantId': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
        'MerchantKey': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
        'Content-Type': 'application/json',
    }
# TODO: INT_CURRENCIES é necessário?
INT_CURRENCIES = [
    u'BRL', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
]


class PaymentTransactionCielo(models.Model):
    _inherit = 'payment.transaction'

    def _create_cielo_charge(self, acquirer_ref=None, tokenid=None, email=None):
        api_url_charge = 'https://%s/1/sales' % (self.acquirer_id._get_cielo_api_url())

        if self.payment_token_id.card_brand == 'mastercard':
            self.payment_token_id.card_brand = 'master'

        charge_params = {
           #  TODO: MerchantOrderId - Numero de identificação do Pedido.
           "MerchantOrderId":"2014111703",
           "Customer":{
              "Name": self.partner_id.name
           },
           "Payment":{
             "Type":"CreditCard",
             "Amount": self.amount * 100,
             "Installments":1,
             # TODO: SoftDescriptor - Texto impresso na fatura bancaria comprador. Deve ser preenchido de acordo com os dados do sub Merchant.
             "SoftDescriptor":"123456789ABCD",
             "CreditCard":{
                 "CardNumber": self.payment_token_id.card_number,
                 "Holder": self.payment_token_id.card_holder,
                 "ExpirationDate":self.payment_token_id.card_exp,
                 "SecurityCode":self.payment_token_id.card_cvc,
                 "Brand":self.payment_token_id.card_brand,
                 "CardOnFile":{
                    "Usage": "Used",
                    "Reason":"Unscheduled"
                 }
             }
           }
        }

        # charge_params = {
        #     'amount': int(self.amount if self.currency_id.name in INT_CURRENCIES else float_round(self.amount * 100, 2)),
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

        _logger.info('_create_cielo_charge: Sending values to URL %s, values:\n%s', api_url_charge, pprint.pformat(charge_params))
        r = requests.post(api_url_charge,
                          auth=(self.acquirer_id.cielo_secret_key, ''),
                          json=charge_params,
                          headers=CIELO_HEADERS)
        # TODO: Interpretar modelo de retorno em caso de erro (atualmente uma compra não autorizada da erro pois a resposta r não aceita o método json() )
        # TODO: Salvar todos os dados de retorno em seus respectivos campos (talvez criar novos para maior controle)
        # TODO: IMPORTANTE deletar informações do cartão e setar active=false pra não aparecer na lista de cartões salvos
        res = r.json()
        _logger.info('_create_cielo_charge: Values received:\n%s', pprint.pformat(res))
        return res

    @api.multi
    def cielo_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        result = self._create_cielo_charge(acquirer_ref=self.payment_token_id.acquirer_ref, email=self.partner_email)
        return self._cielo_s2s_validate_tree(result)


    @api.multi
    def _cielo_s2s_validate_tree(self, tree):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info('Cielo: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        status = tree.get('Payment').get('Status')
        if status == 1:
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': tree.get('id'),
            })
            self._set_transaction_done()
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
