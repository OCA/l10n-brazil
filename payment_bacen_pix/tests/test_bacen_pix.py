# Copyright 2023 KMEE
# License MIT - See https://opensource.org/license/mit

import logging
import os
import time
from datetime import datetime

import vcr

import odoo

from odoo.addons.payment.tests.common import PaymentAcquirerCommon

_logger = logging.getLogger(__name__)

# from odoo.exceptions import ValidationError


class BacenCommon(PaymentAcquirerCommon):
    def setUp(self):
        super(BacenCommon, self).setUp()


@odoo.tests.tagged("post_install", "-at_install")
class BacenTest(BacenCommon):
    # TESTE SUCESSO
    @vcr.use_cassette(os.path.dirname(__file__) + "/fixtures/test_pix_bacen.yaml")
    def test_bacen_pix(self):
        payment_acquirer = None
        tx = None
        # try:
        payment_acquirer = self.env["payment.acquirer"].create(
            {
                "name": "teste",
                "provider": "bacenpix",
                "bacenpix_email_account": "teste@testando.com",
                "bacenpix_client_id": "eyJpZCI6ImY2NmZlYmEtYThmNC0iLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6NDExNDksInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoxfQ",
                "bacenpix_client_secret": "eyJpZCI6IjY2NjUwZjUtZGY4Ny00NGM0IiwiY29kaWdvUHVibGljYWRvciI6MCwiY29kaWdvU29mdHdhcmUiOjQxMTQ5LCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6MSwic2VxdWVuY2lhbENyZWRlbmNpYWwiOjEsImFtYmllbnRlIjoiaG9tb2xvZ2FjYW8iLCJpYXQiOjE2NTk3MDk0ODUyODZ9",
                "bacenpix_dev_app_key": "d27bf7790affab30136fe17de0050d56b9a1a5bc",
                "bacen_pix_basic": "Basic ZXlKcFpDSTZJbVkyTm1abFltRXRZVGhtTkMwaUxDSmpiMlJwWjI5UWRXSnNhV05oWkc5eUlqb3dMQ0pqYjJScFoyOVRiMlowZDJGeVpTSTZOREV4TkRrc0luTmxjWFZsYm1OcFlXeEpibk4wWVd4aFkyRnZJam94ZlE6ZXlKcFpDSTZJalkyTmpVd1pqVXRaR1k0TnkwME5HTTBJaXdpWTI5a2FXZHZVSFZpYkdsallXUnZjaUk2TUN3aVkyOWthV2R2VTI5bWRIZGhjbVVpT2pReE1UUTVMQ0p6WlhGMVpXNWphV0ZzU1c1emRHRnNZV05oYnlJNk1Td2ljMlZ4ZFdWdVkybGhiRU55WldSbGJtTnBZV3dpT2pFc0ltRnRZbWxsYm5SbElqb2lhRzl0YjJ4dloyRmpZVzhpTENKcFlYUWlPakUyTlRrM01EazBPRFV5T0RaOQ==",
            }
        )
        time.sleep(2)
        # Create transaction
        tx = self.env["payment.transaction"].create(
            {
                "bacenpix_date_due": datetime.now(),
                "bacenpix_currency": "BRL",
                "bacenpix_amount": 42.42,
            }
        )
        # except Exception as e:
        #    _logger.warning(e)
        values = {
            "partner_id": 1,
            "acquirer_id": "bacenpix",
            "invoice_ids": 2,
            "reference": 321,
            "amount": 42.42,
            "partner_name": "Fulano",
        }

        payment_acquirer.bacen_pix_get_token()
        res = tx.bacenpix_create(values)

        self.assertEqual(res.state_message, 0)


# """  # Testes de ERRO do Token
# @vcr.use_cassette(os.path.dirname(__file__) + "/fixtures/test_pix_bacen_fail_token.yaml")
# def test_bacen_pix_fail_token(self):
#     self.bacen.write({
#         'bacenpix_client_id' : 'eyJpZCI6ImY2NmZlYmEtYThmNC0iLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6NDExNDksInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoxfQ',
#         'bacenpix_client_secret': 'wrongclientsecret',
#         'bacenpix_dev_app_key': 'd27bf7790affab30136fe17de0050d56b9a1a5bc',
#         'bacen_pix_basic': 'Basic ZXlKcFpDSTZJbVkyTm1abFltRXRZVGhtTkMwaUxDSmpiMlJwWjI5UWRXSnNhV05oWkc5eUlqb3dMQ0pqYjJScFoyOVRiMlowZDJGeVpTSTZOREV4TkRrc0luTmxjWFZsYm1OcFlXeEpibk4wWVd4aFkyRnZJam94ZlE6ZXlKcFpDSTZJalkyTmpVd1pqVXRaR1k0TnkwME5HTTBJaXdpWTI5a2FXZHZVSFZpYkdsallXUnZjaUk2TUN3aVkyOWthV2R2VTI5bWRIZGhjbVVpT2pReE1UUTVMQ0p6WlhGMVpXNWphV0ZzU1c1emRHRnNZV05oYnlJNk1Td2ljMlZ4ZFdWdVkybGhiRU55WldSbGJtTnBZV3dpT2pFc0ltRnRZbWxsYm5SbElqb2lhRzl0YjJ4dloyRmpZVzhpTENKcFlYUWlPakUyTlRrM01EazBPRFV5T0RaOQ==',
#     })
#     self.bacen.bacen_pix_get_token()
#
#        self.assertEqual(self.payment_acquirer.bacenpix_api_key, "Error")
# """
