# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class CieloController(http.Controller):

    @http.route('/payment/cielo/get_provider_info', type='json', auth='public')
    def cielo_get_provider_info(self, provider_id):
        """ Return public information on the provider.

        :param int provider_id: The provider handling the transaction, as a `payment.provider` id
        :return: Information on the provider, namely: the state, payment method type, login ID, and
                 public client key
        :rtype: dict
        """
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id).exists()
        return {
            'state': provider_sudo.state,
            # TODO tipo de transação, debito, credito, pix e etc.... (deveria ficar na transação)
            'payment_type': provider_sudo.payment_type, 
        }
    
    @http.route('/payment/cielo/payment', type='json', auth='public')
    def cielo_payment(self, reference, partner_id, access_token):
        """ Make a payment request and handle the response.

        :param str reference: The reference of the transaction
        :param int partner_id: The partner making the transaction, as a `res.partner` id
        :param str access_token: The access token used to verify the provided values
        :return: None
        """
        # Check that the transaction details have not been altered
        if not payment_utils.check_access_token(access_token, reference, partner_id):
            raise ValidationError("Authorize.Net: " + _("Received tampered payment request data."))

        # Make the payment request to Authorize.Net
        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        response_content = tx_sudo._authorize_create_transaction_request(opaque_data)

        # Handle the payment request response
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            reference, pprint.pformat(response_content)
        )
        tx_sudo._handle_notification_data('authorize', {'response': response_content})






    # ====================================















    @http.route(['/payment/cielo/s2s/create_json_3ds'], type='json',
                auth='public', csrf=False, website=True)
    def cielo_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        if not kwargs.get('partner_id'):
            kwargs['partner_id'] = request.env.user.partner_id.id
        token = request.env['payment.acquirer'].browse(
            int(kwargs.get('acquirer_id'))).s2s_process(kwargs)

        if not token:
            res = {
                'result': False,
                }
            return res

        res = {
            'result': True,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': False,
            }

        return res

    @http.route(['/payment/cielo/s2s/create_json'], type='json', auth='public')
    def cielo_s2s_create_json(self, **kwargs):
        acquirer_id = int(kwargs.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        if not kwargs.get('partner_id'):
            kwargs['partner_id'] = request.env.user.partner_id.id
        return acquirer.s2s_process(kwargs).id

    @http.route(['/payment/cielo/s2s/create'], type='http', auth='public')
    def cielo_s2s_create(self, **post):
        acquirer_id = int(post.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        error = None
        try:
            acquirer.s2s_process(post)
        except Exception as e:
            error = str(e)

        return_url = post.get('return_url', '/')
        if error:
            separator = '?' if werkzeug.urls.url_parse(
                return_url).query == '' else '&'
            return_url += '{}{}'.format(separator, werkzeug.urls.url_encode(
                {'error': error}))

        return werkzeug.utils.redirect(return_url)

    @http.route(['/payment/cielo/s2s/create_json_3ds'], type='json',
                auth='public', csrf=False)
    def cielo_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        if not kwargs.get('partner_id'):
            kwargs['partner_id'] = request.env.user.partner_id.id
        token = request.env['payment.acquirer'].browse(
            int(kwargs.get('acquirer_id'))).s2s_process(kwargs)

        if not token:
            res = {
                'result': False,
                }
            return res

        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': False,
            }

        if verify_validity is not False:
            token.validate()
            res['verified'] = token.verified

        return res

    @http.route(['/payment/cielo/create_charge'], type='json', auth='public')
    def cielo_create_charge(self, **post):
        """ Create a payment transaction

        Expects the result from the user input from checkout.js popup"""
        TX = request.env['payment.transaction']
        tx = None
        if post.get('tx_ref'):
            tx = TX.sudo().search([('reference', '=', post['tx_ref'])])
        if not tx:
            tx_id = (post.get('tx_id') or request.session.get(
                'sale_transaction_id') or request.session.get(
                'website_payment_tx_id'))
            tx = TX.sudo().browse(int(tx_id))
        if not tx:
            raise werkzeug.exceptions.NotFound()

        cielo_token = post['token']
        response = None
        if tx.type == 'form_save' and tx.partner_id:
            payment_token_id = request.env['payment.token'].sudo().create({
                'acquirer_id': tx.acquirer_id.id,
                'partner_id': tx.partner_id.id,
                'cielo_token': cielo_token
                })
            tx.payment_token_id = payment_token_id
            response = tx._create_cielo_charge(
                acquirer_ref=payment_token_id.acquirer_ref,
                email=cielo_token['email'])
        else:
            response = tx._create_cielo_charge(
                tokenid=cielo_token['id'], email=cielo_token['email'])
        _logger.info('Cielo: entering form_feedback with post data %s',
                     pprint.pformat(response))
        if response:
            request.env['payment.transaction'].sudo().with_context(
                lang=None).form_feedback(response, 'cielo')
        # add the payment transaction into the session to let the page
        # /payment/process to handle it
        PaymentProcessing.add_payment_transaction(tx)
        return "/payment/process"
