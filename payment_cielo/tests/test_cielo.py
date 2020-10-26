# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest
import odoo
from odoo import fields
from odoo.addons.payment.tests.common import PaymentAcquirerCommon
from odoo.tools import mute_logger


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

    def test_10_cielo_s2s(self):
        self.assertEqual(self.cielo.environment, 'test',
                         'test without test environment')

        # Add Cielo credentials
        self.cielo.write({
            'cielo_merchant_id': 'be87a4be-a40d-4a2d-b2c8-b8b6cc19cddd',
            'cielo_merchant_key': 'POHAWRXFBSIXTMTFVBCYSKNWZBMOATDNYUQDGBUE',
            })

        # Create payment meethod for Cielo
        payment_token = self.env['payment.token'].create({
            'acquirer_id': self.cielo.id,
            'partner_id': self.buyer_id,
            'cc_number': '4024007197692931',
            'cc_expiry': '02 / 26',
            'cc_brand': 'visa',
            'cvc': '111',
            'cc_holder_name': 'Johndoe',
            })

        # Create transaction
        tx = self.env['payment.transaction'].create({
            'reference': 'test_ref_%s' % fields.date.today(),
            'currency_id': self.currency_euro.id,
            'acquirer_id': self.cielo.id,
            'partner_id': self.buyer_id,
            'payment_token_id': payment_token.id,
            'type': 'server2server',
            'amount': 115.0
            })
        tx.cielo_s2s_do_transaction()
        self.assertEqual(tx.state, 'authorized',
                         'transaction state should be authorized')
        tx.action_capture()
        self.assertEqual(tx.state, 'done',
                         'transaction state should be done')
        tx.cielo_s2s_void_transaction()
        self.assertEqual(tx.state, 'done',
                         'transaction state should be done')

    @unittest.skip(
        "as the test is post-install and because payment_strip_sca changes"
        "the code logic and is automatically installed, this test is invalid.")
    def test_30_cielo_form_management(self):
        self.assertEqual(self.cielo.environment, 'test',
                         'test without test environment')

        # typical data posted by Cielo after client has successfully paid
        cielo_post_data = {
            u'amount': 470000,
            u'amount_refunded': 0,
            u'application_fee': None,
            u'balance_transaction': u'txn_172xfnGMfVJxozLwssrsQZyT',
            u'captured': True,
            u'created': 1446529775,
            u'currency': u'eur',
            u'customer': None,
            u'description': None,
            u'destination': None,
            u'dispute': None,
            u'failure_code': None,
            u'failure_message': None,
            u'fraud_details': {},
            u'id': u'ch_172xfnGMfVJxozLwEjSfpfxD',
            u'invoice': None,
            u'livemode': False,
            u'metadata': {u'reference': u'SO100-1'},
            u'object': u'charge',
            u'paid': True,
            u'receipt_email': None,
            u'receipt_number': None,
            u'refunded': False,
            u'refunds': {
                u'data': [],
                u'has_more': False,
                u'object': u'list',
                u'total_count': 0,
                u'url':
                    u'/v1/charges/ch_172xfnGMfVJxozLwEjSfpfxD/refunds'
                },
            u'shipping': None,
            u'source': {
                u'address_city': None,
                u'address_country': None,
                u'address_line1': None,
                u'address_line1_check': None,
                u'address_line2': None,
                u'address_state': None,
                u'address_zip': None,
                u'address_zip_check': None,
                u'brand': u'Visa',
                u'country': u'US',
                u'customer': None,
                u'cvc_check': u'pass',
                u'dynamic_last4': None,
                u'exp_month': 2,
                u'exp_year': 2022,
                u'fingerprint': u'9tJA9bUEuvEb3Ell',
                u'funding': u'credit',
                u'id': u'card_172xfjGMfVJxozLw1QO6gYNM',
                u'last4': u'4242',
                u'metadata': {},
                u'name': u'norbert.buyer@example.com',
                u'object': u'card',
                u'tokenization_method': None
                },
            u'statement_descriptor': None,
            u'status': u'succeeded'
            }

        tx = self.env['payment.transaction'].create({
            'amount': 4700.0,
            'acquirer_id': self.cielo.id,
            'currency_id': self.currency_euro.id,
            'reference': 'SO100-1',
            'partner_name': 'Norbert Buyer',
            'partner_country_id': self.country_france.id
            })

        # validate it
        tx.form_feedback(cielo_post_data, 'Cielo')
        self.assertEqual(tx.state, 'done',
                         'Cielo: validation did not put tx into done state')
        self.assertEqual(tx.acquirer_reference, cielo_post_data.get('id'),
                         'cielo: validation did not update tx id')
        cielo_post_data['metadata']['reference'] = u'SO100-2'
        # reset tx
        tx = self.env['payment.transaction'].create({
            'amount': 4700.0,
            'acquirer_id': self.cielo.id,
            'currency_id': self.currency_euro.id,
            'reference': 'SO100-2',
            'partner_name': 'Norbert Buyer',
            'partner_country_id': self.country_france.id
            })
        # simulate an error
        cielo_post_data['status'] = 'error'
        cielo_post_data.update({
            u'error': {
                u'message': u"Your card's expiration year is invalid.",
                u'code': u'invalid_expiry_year', u'type': u'card_error',
                u'param': u'exp_year'
                }
            })
        with mute_logger('odoo.addons.payment_cielo.models.payment'):
            with mute_logger('odoo.addons.payment_cielo_sca.models.payment'):
                tx.form_feedback(cielo_post_data, 'cielo')
        # check state
        self.assertEqual(tx.state, 'cancel',
                         'Cielo: erroneous validation did not put tx into '
                         'error state')
