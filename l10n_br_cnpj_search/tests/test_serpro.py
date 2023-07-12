# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time  # You can't send multiple requests at the same time in trial version

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestCnpjCommon


@tagged("post_install", "-at_install")
class TestTestSerPro(TestCnpjCommon):
    def setUp(self):
        super(TestTestSerPro, self).setUp()

        self.set_param("cnpj_provider", "serpro")
        self.set_param("serpro_token", "06aef429-a981-3ec5-a1f8-71d38d86481e")
        self.set_param("serpro_trial", True)
        self.set_param("serpro_schema", "basica")

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
        self.assertEqual(dummy_basica.equity_capital, 0)
        self.assertEqual(dummy_basica.cnae_main_id.code, "6204-0/00")

    def test_serpro_not_found(self):
        # Na versão Trial só há alguns registros de CNPJ cadastrados
        invalid = self.model.create(
            {"name": "invalid", "cnpj_cpf": "44.356.113/0001-08"}
        )
        invalid._onchange_cnpj_cpf()

        time.sleep(2)  # Pause
        with self.assertRaises(ValidationError):
            invalid.search_cnpj()

    def assert_socios(self, partner, expected_cnpjs):
        socios = self.model.search_read(
            [("id", "in", partner.child_ids.ids)],
            fields=["name", "cnpj_cpf", "company_type"],
        )

        for s in socios:
            s.pop("id")

        expected_socios = [
            {
                "name": "Joana Alves Mundim Pena",
                "cnpj_cpf": expected_cnpjs["Joana"],
                "company_type": "person",
            },
            {
                "name": "Luiza Aldenora",
                "cnpj_cpf": expected_cnpjs["Aldenora"],
                "company_type": "person",
            },
            {
                "name": "Luiza Araujo De Oliveira",
                "cnpj_cpf": expected_cnpjs["Araujo"],
                "company_type": "person",
            },
            {
                "name": "Luiza Barbosa Bezerra",
                "cnpj_cpf": expected_cnpjs["Barbosa"],
                "company_type": "person",
            },
            {
                "name": "Marcelo Antonio Barros De Cicco",
                "cnpj_cpf": expected_cnpjs["Marcelo"],
                "company_type": "person",
            },
        ]

        self.assertEqual(socios, expected_socios)

    def test_serpro_empresa(self):
        self.model.search([("cnpj_cpf", "=", "34.238.864/0001-68")]).unlink()
        self.set_param("serpro_schema", "empresa")

        dummy_empresa = self.model.create(
            {"name": "Dummy Empresa", "cnpj_cpf": "34.238.864/0001-68"}
        )

        time.sleep(2)  # Pause
        dummy_empresa._onchange_cnpj_cpf()
        dummy_empresa.search_cnpj()

        expected_cnpjs = {
            "Joana": "23982012600",
            "Aldenora": "76822320300",
            "Araujo": "07119488449",
            "Barbosa": "13946994415",
            "Marcelo": "00031298702",
        }

        self.assert_socios(dummy_empresa, expected_cnpjs)

    def test_serpro_qsa(self):
        self.model.search([("cnpj_cpf", "=", "54447820000155")]).unlink()
        self.set_param("serpro_schema", "qsa")

        dummy_qsa = self.model.create(
            {"name": "Dummy QSA", "cnpj_cpf": "34.238.864/0001-68"}
        )

        time.sleep(2)  # Pause
        dummy_qsa._onchange_cnpj_cpf()
        dummy_qsa.search_cnpj()

        expected_cnpjs = {
            "Joana": False,
            "Aldenora": False,
            "Araujo": False,
            "Barbosa": False,
            "Marcelo": False,
        }

        self.assert_socios(dummy_qsa, expected_cnpjs)
