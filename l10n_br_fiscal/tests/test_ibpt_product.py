# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestIbptProduct(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.company = self._create_compay()
        self._switch_user_company(self.env.user, self.company)
        self.ncm_85030010 = self.env.ref("l10n_br_fiscal.ncm_85030010")
        self.ncm_85014029 = self.env.ref("l10n_br_fiscal.ncm_85014029")
        self.product_tmpl_model = self.env["product.template"]
        self.product_tmpl_1 = self._create_product_tmpl(
            name="Product Test 1 - With NCM: 8503.00.10", ncm=self.ncm_85030010
        )

        self.product_tmpl_2 = self._create_product_tmpl(
            name="Product Test 2 - With NCM: 8503.00.10", ncm=self.ncm_85030010
        )

        self.product_tmpl_3 = self._create_product_tmpl(
            name="Product Test 3 - With NCM: 8501.40.29", ncm=self.ncm_85014029
        )

        self.tax_estimate_model = self.env["l10n_br_fiscal.tax.estimate"]
        self.ncm_model = self.env["l10n_br_fiscal.ncm"]

    @classmethod
    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write({
            'company_ids': [(6, 0, (company + user.company_ids).ids)],
            'company_id': company.id,
        })

    @classmethod
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

    @classmethod
    def _create_product_tmpl(self, name, ncm):
        # Creating a product
        product = self.product_tmpl_model.create({"name": name, "ncm_id": ncm.id})
        return product

    def test_update_ibpt_product(self):
        """Check tax estimate update"""
        self.ncm_85030010.action_ibpt_inquiry()
        self.assertTrue(self.ncm_85030010.tax_estimate_ids)

        self.ncm_85014029.action_ibpt_inquiry()
        self.assertTrue(self.ncm_85014029.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("ncm_id", "in", (self.ncm_85030010.id, self.ncm_85014029.id))]
        ).unlink()

    def test_ncm_count_product_template(self):
        """Check product template relation with NCM"""
        self.assertEquals(self.ncm_85030010.product_tmpl_qty, 2)
        self.assertEquals(self.ncm_85014029.product_tmpl_qty, 1)

    def test_update_scheduled(self):
        """Check NCM update scheduled"""
        ncms = self.ncm_model.search(
            [("id", "in", (self.ncm_85030010.id, self.ncm_85014029.id))]
        )
        ncms._scheduled_update()

        self.assertTrue(self.ncm_85030010.tax_estimate_ids)
        self.assertTrue(self.ncm_85014029.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("ncm_id", "in", (self.ncm_85030010.id, self.ncm_85014029.id))]
        ).unlink()
