# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo
from odoo.addons.payment.tests.common import PaymentAcquirerCommon
import time
import logging
import os

_logger = logging.getLogger(__name__)

class PagseguroCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(PagseguroCommon, self).setUp()

        self.currency_brl = self.env['res.currency'].search([('name', '=', 'BRL')], limit=1)
        self.assertTrue(self.currency_brl.active, 'BRL currency deactivated')
        self.pagseguro = self.env.ref('payment_pagseguro.payment_acquirer_pagseguro')
        self.pagseguro.write({
            'pagseguro_email': 'mileo@kmee.com.br',
            'pagseguro_token': 'A5BB2E295B2740558E84B62821DCB91E',
            }) # TODO Change to comprador teste credentials

@odoo.tests.tagged('post_install', '-at_install')
class PagseguroTest(PagseguroCommon):

    def test_10_pagseguro_s2s_capture(self):
        self.assertEqual(self.pagseguro.environment, 'test',
                         'test without test environment')

         # Create payment meethod for Pagseguro
        try:
            payment_token = self.env['payment.token'].create({
                'acquirer_id': self.pagseguro.id,
                'partner_id': self.buyer_id,
                'cc_number': '4111111111111111',
                'cc_expiry': '12/2030',
                'cc_brand': 'visa',
                'cc_cvc': '123',
                'cc_holder_name': 'Johndoe',
                })
            time.sleep(2)
            # Create transaction
            transaction = self.env['payment.transaction'].create({
                'reference': 'test_ref_10_p',
                'currency_id': self.currency_brl.id,
                'acquirer_id': self.pagseguro.id,
                'partner_id': self.buyer_id,
                'payment_token_id': payment_token.id,
                'type': 'server2server',
                'amount': 115.0
                })
        except Exception as e:
            _logger.warning(e)

        transaction.pagseguro_s2s_do_transaction()
        self.assertEqual(transaction.state, 'authorized',
                         'transaction state should be authorized')

        time.sleep(3)
        transaction.action_capture()
        self.assertEqual(transaction.state, 'done',
                         'transaction state should be done')

    # def test_10_pagseguro_s2s_void(self):
    #     self.assertEqual(self.pagseguro.environment, 'test',
    #                      'test without test environment')

    #      # Create payment meethod for Pagseguro
    #     try:
    #         payment_token = self.env['payment.token'].create({
    #             'acquirer_id': self.pagseguro.id,
    #             'partner_id': self.buyer_id,
    #             'cc_number': '4111111111111111',
    #             'cc_expiry': '12/2030',
    #             'cc_brand': 'visa',
    #             'cc_cvc': '123',
    #             'cc_holder_name': 'Johndoe',
    #             })
    #         time.sleep(2)
    #         # Create transaction
    #         transaction = self.env['payment.transaction'].create({
    #             'reference': 'test_ref_10_p',
    #             'currency_id': self.currency_brl.id,
    #             'acquirer_id': self.pagseguro.id,
    #             'partner_id': self.buyer_id,
    #             'payment_token_id': payment_token.id,
    #             'type': 'server2server',
    #             'amount': 115.0
    #             })
    #     except Exception as e:
    #         _logger.warning(e)

    #     transaction.pagseguro_s2s_do_transaction()
    #     self.assertEqual(transaction.state, 'authorized',
    #                      'transaction state should be authorized')

    #     time.sleep(3)
    #     transaction.action_void()
    #     self.assertEqual(transaction.state, 'cancel',
    #                      'transaction state should be done')
