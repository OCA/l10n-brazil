# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo
from odoo.addons.payment.tests.common import PaymentAcquirerCommon
import time
import logging
import vcr
import os

_logger = logging.getLogger(__name__)


class CieloCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(CieloCommon, self).setUp()
        self.cielo = self.env.ref('payment_cielo.payment_acquirer_cielo')
        self.cielo.write({
            'cielo_merchant_id': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
            'cielo_merchant_key': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
            })


@odoo.tests.tagged('post_install', '-at_install')
class CieloTest(CieloCommon):

    @vcr.use_cassette(os.path.dirname(__file__) +
                      '/fixtures/test_10_cielo_s2s.yaml',
                      match_on=['method', 'scheme', 'host', 'port', 'path',
                                'query', 'body'],
                      filter_post_data_parameters=['MerchantOrderId',
                                                   'SoftDescriptor'])
    def test_10_cielo_s2s(self):
        self.assertEqual(self.cielo.environment, 'test',
                         'test without test environment')

        # Add Cielo credentials
        self.cielo.write({
            'cielo_merchant_id': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
            'cielo_merchant_key': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
            })

        # Create payment meethod for Cielo
        try:
            payment_token = self.env['payment.token'].create({
                'acquirer_id': self.cielo.id,
                'partner_id': self.buyer_id,
                'cc_number': '4024007197692931',
                'cc_expiry': '02 / 26',
                'cc_brand': 'visa',
                'cvc': '111',
                'cc_holder_name': 'Johndoe',
                })
            time.sleep(2)
            # Create transaction
            tx = self.env['payment.transaction'].create({
                'reference': 'test_ref_10_c',
                'currency_id': self.currency_euro.id,
                'acquirer_id': self.cielo.id,
                'partner_id': self.buyer_id,
                'payment_token_id': payment_token.id,
                'type': 'server2server',
                'amount': 115.0
                })
        except Exception as e:
            _logger.warning(e)

        tx.cielo_s2s_do_transaction()
        self.assertEqual(tx.state, 'authorized',
                         'transaction state should be authorized')
        time.sleep(3)
        tx.action_capture()
        self.assertEqual(tx.state, 'done',
                         'transaction state should be done')
        time.sleep(3)
        tx.cielo_s2s_void_transaction()
        self.assertEqual(tx.state, 'done',
                         'transaction state should be done')

    def test_20_cielo_s2s(self):
        # Test invalid card
        self.assertEqual(self.cielo.environment, 'test',
                         'test without test environment')

        # Add Cielo credentials
        self.cielo.write({
            'cielo_merchant_id': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
            'cielo_merchant_key': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
            })

        # Create payment meethod for Cielo
        try:
            payment_token = self.env['payment.token'].create({
                'acquirer_id': self.cielo.id,
                'partner_id': self.buyer_id,
                'cc_number': '5324007197691291',
                'cc_expiry': '02 / 12',
                'cc_brand': 'visa',
                'cvc': '111',
                'cc_holder_name': 'Johndoe',
                })
            time.sleep(3)

        # Create transaction todo test
            tx = self.env['payment.transaction'].create({
                'reference': 'test_ref_10_c',
                'currency_id': self.currency_euro.id,
                'acquirer_id': self.cielo.id,
                'partner_id': self.buyer_id,
                'payment_token_id': payment_token.id,
                'type': 'server2server',
                'amount': 115.0
                })
        except Exception as e:
            _logger.warning(e)

        try:
            tx.cielo_s2s_do_transaction()
        except Exception as e:
            _logger.warning(e)

        with self.assertRaises(NameError):
            self.assertEqual(tx, None)
