# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.addons.l10n_br_cnpj_search.tests.common import (
    TestCnpjCommon,
)


class TestCRMReceitaws(TestCnpjCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.crm_lead_model = cls.env["crm.lead"]
        cls.res_partner_model = cls.env["res.partner"]
        cls.crm_lead_1 = cls.crm_lead_model.create({"name": "Jamanta"})

    def test_convert_to_oportunity(self):
        # self.crm_lead_1._onchange_cnpj_cpf()
        mocked_response = self.mocked_response_ws_1
        mocked_response["atividades_secundarias"] = [
            {
                "code": "62.01-5-01",
                "text": "Desenvolvimento de programas de computador sob encomenda",
            },
            {
                "code": "62.03-1-00",
                "text": """Desenvolvimento e licenciamento de programas
                de computador não-customizáveis""",
            },
            {
                "code": "62.09-1-00",
                "text": """Suporte técnico, manutenção e outros
                serviços em tecnologia da informação""",
            },
            {
                "code": "63.11-9-00",
                "text": """Tratamento de dados, provedores de serviços de
                aplicação e serviços de hospedagem na internet""",
            },
            {
                "code": "85.99-6-04",
                "text": "Treinamento em desenvolvimento profissional e gerencial",
            },
        ]
        with mock.patch(
            "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice.CNPJWebservice.validate",
            return_value=mocked_response,
        ):
            self.crm_lead_1.write({"cnpj_cpf": "31.954.065/0001-08"})
            action_wizard = self.crm_lead_1.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard = (
                self.env["partner.search.wizard"]
                .with_context(**wizard_context)
                .create({})
            )
            wizard.action_update_partner()
            self.assertEqual(
                self.crm_lead_1.legal_name,
                "Kilian Macedo Melcher 08777131460",
            )
        self.assertEqual(self.crm_lead_1.street_name, "Rua Luiza Bezerra Motta")
        self.assertEqual(self.crm_lead_1.street2, "Bloco E;Apt 302")
        self.assertEqual(self.crm_lead_1.street_number, "950")
        self.assertEqual(self.crm_lead_1.zip, "58.410-410")
        self.assertEqual(self.crm_lead_1.district, "Catole")
        self.assertEqual(self.crm_lead_1.phone, "(83) 8665-0905")
        self.assertEqual(self.crm_lead_1.state_id.code, "PB")
        self.assertEqual(self.crm_lead_1.equity_capital, 3000.00)
        self.assertEqual(self.crm_lead_1.cnae_main_id.code, "4751-2/01")

        cnaes = [
            "6201-5/01",
            "6203-1/00",
            "6209-1/00",
            "6311-9/00",
            "8599-6/04",
        ]
        cnaes = sorted(cnaes)
        cnae_secondary_codes = [
            cnae.code for cnae in self.crm_lead_1.cnae_secondary_ids
        ]
        cnae_secondary_codes = sorted(cnae_secondary_codes)
        for i in range(0, len(cnae_secondary_codes)):
            self.assertEqual(cnaes[i], cnae_secondary_codes[i])
