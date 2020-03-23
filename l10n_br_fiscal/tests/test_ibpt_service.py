# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestIbptService(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.company = self._create_compay()
        self._switch_user_company(self.env.user, self.company)
        self.nbs_115069000 = self.env.ref("l10n_br_fiscal.nbs_115069000")
        self.nbs_124043300 = self.env.ref("l10n_br_fiscal.nbs_124043300")
        self.product_tmpl_model = self.env["product.template"]
        self.product_tmpl_1 = self._create_product_tmpl(
            name="Service Test 1 - With NBS: 1.1506.90.00",
            nbs=self.nbs_115069000)

        self.product_tmpl_2 = self._create_product_tmpl(
            name="Product Test 2 - With NBS: 1.1506.90.00",
            nbs=self.nbs_115069000)

        self.product_tmpl_3 = self._create_product_tmpl(
            name="Product Test 3 - With NBS: 1.2404.33.00",
            nbs=self.nbs_124043300)

        self.tax_estimate_model = self.env["l10n_br_fiscal.tax.estimate"]
        self.nbs_model = self.env["l10n_br_fiscal.nbs"]

    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write({
            'company_ids': [(6, 0, (company + user.company_ids).ids)],
            'company_id': company.id,
        })

    def _create_compay(self):
        # Creating a company
        company = self.env["res.company"].create(
            {
                "name": "Company Test Fiscal BR",
                "cnpj_cpf": "02.960.895/0002-12",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_es").id,
                "ibpt_api": True,
                "ibpt_update_days": 0,
                "ibpt_token": (
                    "dsaaodNP5i6RCu007nPQjiOPe5XIefnx"
                    "StS2PzOV3LlDRVNGdVJ5OOUlwWZhjFZk"
                ),
            }
        )
        return company

    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    def _create_product_tmpl(self, name, nbs):
        # Creating a product
        product = self.product_tmpl_model.create({
            "name": name,
            "nbs_id": nbs.id})
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
        self.assertEquals(self.nbs_115069000.product_tmpl_qty, 2)
        self.assertEquals(self.nbs_124043300.product_tmpl_qty, 1)

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
