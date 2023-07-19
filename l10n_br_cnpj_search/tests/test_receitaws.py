# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time  # You can't send multiple requests at the same time in trial version

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_br_cnpj_search.tests.common import TestCnpjCommon


@tagged("post_install", "-at_install")
class TestReceitaWS(TestCnpjCommon):
    def setUp(self):
        super(TestReceitaWS, self).setUp()

        self.set_param("cnpj_provider", "receitaws")

    def test_receita_ws_success(self):
        kilian = self.model.create({"name": "Kilian", "cnpj_cpf": "44.356.113/0001-08"})

        kilian._onchange_cnpj_cpf()
        kilian.search_cnpj()

        self.assertEqual(kilian.company_type, "company")
        self.assertEqual(kilian.legal_name, "Kilian Macedo Melcher 08777131460")
        self.assertEqual(kilian.name, "Kilian Macedo Melcher")
        self.assertEqual(kilian.email, "kilian.melcher@gmail.com")
        self.assertEqual(kilian.street_name, "Rua Luiza Bezerra Motta")
        self.assertEqual(kilian.street2, "Bloco E;Apt 302")
        self.assertEqual(kilian.street_number, "950")
        self.assertEqual(kilian.zip, "58.410-410")
        self.assertEqual(kilian.district, "Catole")
        self.assertEqual(kilian.phone, "(83) 8665-0905")
        self.assertEqual(kilian.state_id.code, "PB")
        self.assertEqual(kilian.city_id.name, "Campina Grande")
        self.assertEqual(kilian.equity_capital, 3000)
        self.assertEqual(kilian.cnae_main_id.code, "4751-2/01")

    def test_receita_ws_fail(self):
        invalido = self.model.create({"name": "invalido", "cnpj_cpf": "00000000000000"})
        invalido._onchange_cnpj_cpf()

        time.sleep(2)  # Pause
        with self.assertRaises(ValidationError):
            invalido.search_cnpj()

    def test_receita_ws_multiple_phones(self):
        isla = self.model.create({"name": "Isla", "cnpj_cpf": "92.666.056/0001-06"})
        isla._onchange_cnpj_cpf()

        time.sleep(2)  # Pause
        isla.search_cnpj()

        self.assertEqual(isla.name, "Isla Sementes Ltda.")
        self.assertEqual(isla.phone, "(51) 9852-9561")
        self.assertEqual(isla.mobile, "(51) 2136-6600")
