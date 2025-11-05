# Copyright 2022 KMEE
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_br_cnpj_search.tests.common import TestCnpjCommon


@tagged("post_install", "-at_install")
class TestReceitaWS(TestCnpjCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_param("cnpj_provider", "receitaws")

    def test_receita_ws_success(self):
        kilian = self.model.create(
            {
                "name": "Kilian",
                "cnpj_cpf": "44.356.113/0001-08",
            }
        )

        with mock.patch(
            "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice.CNPJWebservice.validate",
            return_value=self.mocked_response_ws_1,
        ):
            action_wizard = kilian.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            wizard = (
                self.env["partner.search.wizard"]
                .with_context(**wizard_context)
                .create({})
            )
            wizard.action_update_partner()

        self.assertEqual(kilian.company_type, "company")
        self.assertEqual(kilian.legal_name, "Kilian Macedo Melcher 08777131460")
        self.assertEqual(kilian.name, "Kilian Macedo Melcher 08777131460")
        self.assertEqual(kilian.email, "kilian.melcher@gmail.com")
        self.assertEqual(kilian.street_name, "Rua Luiza Bezerra Motta")
        self.assertEqual(kilian.street2, "Bloco E;Apt 302")
        self.assertEqual(kilian.street_number, "950")
        self.assertEqual(kilian.zip, "58.410-410")
        self.assertEqual(kilian.district, "Catole")
        self.assertEqual(kilian.phone, "(83) 8665-0905")
        self.assertEqual(kilian.state_id.code, "PB")
        self.assertEqual(kilian.city_id.name, "Campina Grande")
        self.assertEqual(kilian.city, "Campina Grande")
        self.assertEqual(kilian.equity_capital, 3000)
        self.assertEqual(kilian.cnae_main_id.code, "4751-2/01")

    def test_receita_ws_fail(self):
        with self.assertRaises(ValidationError):
            invalido = self.model.create(
                {"name": "invalido", "cnpj_cpf": "00000000000000"}
            )
            invalido._onchange_cnpj_cpf()
            action_wizard = invalido.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})

    def test_receita_ws_multiple_phones(self):
        with mock.patch(
            "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice.CNPJWebservice.validate",
            return_value=self.mocked_response_ws_2,
        ):
            isla = self.model.create({"name": "Isla", "cnpj_cpf": "92.666.056/0001-06"})
            isla._onchange_cnpj_cpf()

            action_wizard = isla.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            wizard = (
                self.env["partner.search.wizard"]
                .with_context(**wizard_context)
                .create({})
            )
            wizard.action_update_partner()
        self.assertEqual(isla.name.strip(), "Isla Sementes Ltda.")
        self.assertEqual(isla.phone.strip(), "(51) 9852-9561")
        self.assertEqual(isla.mobile.strip(), "(51) 2136-6600")
