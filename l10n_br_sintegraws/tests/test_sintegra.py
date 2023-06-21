# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time  # You can't send multiple requests at the same time in trial version

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestCnpjCommon

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestTestSintegra(TestCnpjCommon):
    def setUp(self):
        super(TestTestSintegra, self).setUp()

        self.set_param_cnpj("cnpj_provider", "receitaws")
        self.set_param("sintegra_token", "C3144731-15F5-4F87-AC74-8887E4900A13")
        self.set_param("ie_search", True)

    def test_sintegra(self):
        dummy = self.model.create({"name": "Dummy", "cnpj_cpf": "06990590000123"})

        time.sleep(2)  # to avoid too many requests
        dummy._onchange_cnpj_cpf()
        dummy.ie_search()

        self.assertEqual(dummy.inscr_est, "149848403115")

    def test_sintegra_ie_search_disabled(self):
        dummy = self.model.create({"name": "Dummy", "cnpj_cpf": "06990590000123"})
        self.set_param("ie_search", False)
        time.sleep(1)  # to avoid too many requests
        with self.assertRaises(UserError):
            dummy._onchange_cnpj_cpf()
            dummy.ie_search()
