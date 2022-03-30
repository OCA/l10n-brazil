# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestIbptService(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls._create_compay()
        cls._switch_user_company(cls.env.user, cls.company)
        cls.nbs_115069000 = cls.env.ref("l10n_br_fiscal.nbs_115069000")
        cls.nbs_124043300 = cls.env.ref("l10n_br_fiscal.nbs_124043300")
        cls.product_tmpl_model = cls.env["product.template"]
        cls.product_tmpl_1 = cls._create_product_tmpl(
            name="Service Test 1 - With NBS: 1.1506.90.00", nbs=cls.nbs_115069000
        )

        cls.product_tmpl_2 = cls._create_product_tmpl(
            name="Product Test 2 - With NBS: 1.1506.90.00", nbs=cls.nbs_115069000
        )

        cls.product_tmpl_3 = cls._create_product_tmpl(
            name="Product Test 3 - With NBS: 1.2404.33.00", nbs=cls.nbs_124043300
        )

        cls.tax_estimate_model = cls.env["l10n_br_fiscal.tax.estimate"]
        cls.nbs_model = cls.env["l10n_br_fiscal.nbs"]

    @classmethod
    def _switch_user_company(cls, user, company):
        """Add a company to the user's allowed & set to current."""
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    @classmethod
    def _create_compay(cls):
        # Creating a company
        company = cls.env["res.company"].create(
            {
                "name": "Company Test Fiscal BR",
                "cnpj_cpf": "02.960.895/0002-12",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_es").id,
                "ibpt_api": True,
                "ibpt_update_days": 0,
                "ibpt_token": (
                    "dsaaodNP5i6RCu007nPQjiOPe5XIefnx"
                    "StS2PzOV3LlDRVNGdVJ5OOUlwWZhjFZk"
                ),
            }
        )
        return company

    @classmethod
    def _create_product_tmpl(cls, name, nbs):
        # Creating a product
        product = cls.product_tmpl_model.create({"name": name, "nbs_id": nbs.id})
        return product

    def test_update_ibpt_service(self):
        """Check tax estimate update"""
        self.nbs_115069000.action_ibpt_inquiry()
        self.assertTrue(self.nbs_115069000.tax_estimate_ids)

        self.nbs_124043300.action_ibpt_inquiry()
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("nbs_id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        ).unlink()

    def test_nbs_count_product_template(self):
        """Check product template relation with NBS"""
        self.assertEqual(self.nbs_115069000.product_tmpl_qty, 2)
        self.assertEqual(self.nbs_124043300.product_tmpl_qty, 1)

    def test_update_scheduled(self):
        """Check NBS update scheduled"""
        nbss = self.nbs_model.search(
            [("id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        )
        nbss._scheduled_update()

        self.assertTrue(self.nbs_115069000.tax_estimate_ids)
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("nbs_id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        ).unlink()
