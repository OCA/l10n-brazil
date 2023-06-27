# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time  # You can't send multiple requests at the same time in trial version

from odoo.tests import HttpCase, tagged

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestTestSintegra(HttpCase):
    def setUp(self):
        super(TestTestSintegra, self).setUp()
        self.model = self.env["res.partner"]
        self.set_param_cnpj("cnpj_provider", "receitaws")
        self.set_param("sintegra_token", "C3144731-15F5-4F87-AC74-8887E4900A13")
        self.set_param("ie_search", "sintegraws")

    def set_param_cnpj(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj_search." + param_name, param_value)
        )

    def set_param(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_ie_search." + param_name, param_value)
        )

    def test_sintegra(self):
        dummy = self.model.create({"name": "Dummy", "cnpj_cpf": "06990590000123"})

        time.sleep(2)  # to avoid too many requests
        dummy._onchange_cnpj_cpf()
        dummy.ie_search()

        self.assertEqual(dummy.inscr_est, "149848403115")
