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


class PaymentAcquirerCielo(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cielo', 'Cielo')])
    cielo_secret_key = fields.Char(required_if_provider='cielo', groups='base.group_user')
    cielo_publishable_key = fields.Char(required_if_provider='cielo', groups='base.group_user')
    cielo_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user')

    @api.multi
    def cielo_s2s_form_validate(self, data):
        self.ensure_one()

        # mandatory fields
        for field_name in ["cc_number", "cvc", "cc_holder_name", "cc_expiry", "cc_brand"]:
            if not data.get(field_name):
                return False
        return True

    @api.model
    def cielo_s2s_form_process(self, data):
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
        # return True

    @api.model
    def _get_cielo_api_url(self):
        #  TODO: Diferenciar URL de testes e produção
        # hml apisandbox.cieloecommerce.cielo.com.br
        # produção api.cieloecommerce.cielo.com.br
        return 'apisandbox.cieloecommerce.cielo.com.br'


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

