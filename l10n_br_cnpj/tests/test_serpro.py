# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time  # You can't send multiple requests at the same time in trial version

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTestSerPro(TransactionCase):
    def setUp(self):
        super(TestTestSerPro, self).setUp()

        self.model = self.env["res.partner"]
        self.set_param("cnpj_provider", "serpro")
        self.set_param("serpro_token", "06aef429-a981-3ec5-a1f8-71d38d86481e")
        self.set_param("serpro_trial", True)
        self.set_param("serpro_schema", "basica")

    def set_param(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj." + param_name, param_value)
        )

    def test_serpro_basica(self):
        dummy_basica = self.model.create(
            {"name": "Dummy Basica", "cnpj_cpf": "34.238.864/0001-68"}
        )

        dummy_basica._onchange_cnpj_cpf()
        dummy_basica.search_cnpj()

        self.assertEqual(dummy_basica.company_type, "company")
        self.assertEqual(
            dummy_basica.legal_name,
            "Uhieqkx Whnhiwd Nh Fixkhuuwphmvx Nh Nwnxu (Uhifix)",
        )
        self.assertEqual(dummy_basica.name, "Uhifix Uhnh")
        self.assertEqual(dummy_basica.email, "EMPRESA@XXXXXX.BR")
        self.assertEqual(dummy_basica.street_name, "Nh Biwmnh Wihw Mxivh")
        self.assertEqual(dummy_basica.street2, "Lote V")
        self.assertEqual(dummy_basica.street_number, "Q.601")
        self.assertEqual(dummy_basica.zip, "70836900")
        self.assertEqual(dummy_basica.district, "Asa Norte")
        self.assertEqual(dummy_basica.phone, "(61) 22222222")
        self.assertEqual(dummy_basica.mobile, "(61) 22222222")
        self.assertEqual(dummy_basica.state_id.code, "DF")
        self.assertEqual(dummy_basica.city_id.name, "Brasília")

    def test_serpro_not_found(self):
        # Na versão Trial só há alguns registros de CNPJ cadastrados
        invalid = self.model.create(
            {"name": "invalid", "cnpj_cpf": "44.356.113/0001-08"}
        )
        invalid._onchange_cnpj_cpf()

        time.sleep(2)  # Pause
        with self.assertRaises(ValidationError):
            invalid.search_cnpj()
