# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestCRMReceitaws(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.crm_lead_model = cls.env["crm.lead"]
        cls.res_partner_model = cls.env["res.partner"]
        cls.crm_lead_1 = cls.crm_lead_model.create({"name": "Jamanta"})

    def test_convert_to_oportunity(self):
        # self.crm_lead_1._onchange_cnpj_cpf()
        self.crm_lead_1.write({"cnpj_cpf": "31.954.065/0001-08"})
        action_wizard = self.crm_lead_1.action_open_cnpj_search_wizard()
        wizard_context = action_wizard.get("context")
        wizard = (
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})
        )
        wizard.action_update_partner()
        self.assertEqual(
            self.crm_lead_1.legal_name,
            "Atacadao Jamanta Ltda",
        )
        self.assertEqual(self.crm_lead_1.name, "Atacadao Jamanta")
        self.assertEqual(self.crm_lead_1.street, "Rodovia Br 393")
        self.assertEqual(self.crm_lead_1.street2, "Km 72")
        self.assertEqual(self.crm_lead_1.street_number, "774")
        self.assertEqual(self.crm_lead_1.zip, "25.887-000")
        self.assertEqual(self.crm_lead_1.district, "Jamapara")
        self.assertEqual(self.crm_lead_1.phone, "(32) 8412-7486")
        self.assertEqual(self.crm_lead_1.mobile, False)
        self.assertEqual(self.crm_lead_1.state_id.code, "RJ")
        self.assertEqual(self.crm_lead_1.equity_capital, 95400.0)
        self.assertEqual(self.crm_lead_1.cnae_main_id.code, "4635-4/02")

        cnaes = [
            "4635-4/99",
            "4646-0/01",
            "4691-5/00",
            "4723-7/00",
            "4729-6/99",
            "4772-5/00",
            "4930-2/02",
        ]
        cnaes = sorted(cnaes)
        cnae_secondary_codes = [
            cnae.code for cnae in self.crm_lead_1.cnae_secondary_ids
        ]
        cnae_secondary_codes = sorted(cnae_secondary_codes)
        for i in range(0, len(cnae_secondary_codes)):
            self.assertEqual(cnaes[i], cnae_secondary_codes[i])
