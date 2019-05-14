# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo.tests import common
from odoo import fields


class TestIbptService(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.company_model = self.env['res.company']
        self.company = self._create_compay()
        self.nbs_115069000 = self.env.ref('fiscal.nbs_115069000')
        self.nbs_124043300 = self.env.ref('fiscal.nbs_124043300')
        self.product_tmpl_model = self.env['product.template']
        self.product_tmpl_1 = self._create_product_tmpl_1()
        self.product_tmpl_2 = self._create_product_tmpl_2()
        self.product_tmpl_3 = self._create_product_tmpl_3()
        self.fiscal_tax_estimate_model = self.env['fiscal.tax.estimate']
        self.fiscal_nbs_model = self.env['fiscal.nbs']

    def _create_compay(self):
        # Creating a company
        company = self.env.ref('base.main_company').write({
            'cnpj_cpf': '02.960.895/0002-12',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_es').id,
            'ibpt_api': True,
            'ibpt_update_days': 0,
            'ibpt_token': ('dsaaodNP5i6RCu007nPQjiOPe5XIefnx'
                           'StS2PzOV3LlDRVNGdVJ5OOUlwWZhjFZk')
        })
        return company

    def _create_product_tmpl_1(self):
        # Creating a product
        product = self.product_tmpl_model.create({
            'name': 'Service Test 1 - With NBS: 1.1506.90.00',
            'nbs_id': self.nbs_115069000.id,
        })
        return product

    def _create_product_tmpl_2(self):
        # Creating a product
        product = self.product_tmpl_model.create({
            'name': 'Product Test 2 - With NBS: 1.1506.90.00',
            'nbs_id': self.nbs_115069000.id,
        })
        return product

    def _create_product_tmpl_3(self):
        # Creating a product
        product = self.product_tmpl_model.create({
            'name': 'Product Test 3 - With NBS: 1.2404.33.00',
            'nbs_id': self.nbs_124043300.id,
        })
        return product

    def test_update_ibpt_service(self):
        """Check tax estimate update"""
        self.nbs_115069000.get_ibpt()
        self.assertTrue(self.nbs_115069000.tax_estimate_ids)

        self.nbs_124043300.get_ibpt()
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        tax_estimates = self.fiscal_tax_estimate_model.search([
            ('nbs_id', 'in', (self.nbs_115069000.id, self.nbs_124043300.id))
        ]).unlink()

    def test_nbs_count_product_template(self):
        """Check product template relation with NBS"""
        self.assertEquals(self.nbs_115069000.product_tmpl_qty, 2)
        self.assertEquals(self.nbs_124043300.product_tmpl_qty, 1)

    def test_update_scheduled(self):
        """Check NBS update scheduled"""
        nbss = self.fiscal_nbs_model.search([
            ('id', 'in', (self.nbs_115069000.id, self.nbs_124043300.id))])
        nbss._scheduled_update()

        self.assertTrue(self.nbs_115069000.tax_estimate_ids)
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        tax_estimates = self.fiscal_tax_estimate_model.search([
            ('nbs_id', 'in', (self.nbs_115069000.id, self.nbs_124043300.id))
        ]).unlink()
