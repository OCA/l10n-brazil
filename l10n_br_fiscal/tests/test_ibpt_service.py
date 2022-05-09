# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_ibpt import TestIbpt


class TestIbptService(TestIbpt):
    @classmethod
    def setUpClass(cls):

        super().setUpClass()
        cls.nbs_115069000 = cls.env.ref("l10n_br_fiscal.nbs_115069000")
        cls.nbs_124043300 = cls.env.ref("l10n_br_fiscal.nbs_124043300")

        cls.product_tmpl_1 = cls._create_service_tmpl(
            name="Service Test 1 - With NBS: 1.1506.90.00", nbs=cls.nbs_115069000
        )

        cls.product_tmpl_2 = cls._create_service_tmpl(
            name="Product Test 2 - With NBS: 1.1506.90.00", nbs=cls.nbs_115069000
        )

        cls.product_tmpl_3 = cls._create_service_tmpl(
            name="Product Test 3 - With NBS: 1.2404.33.00", nbs=cls.nbs_124043300
        )

    def test_update_ibpt_service(self):
        """Check tax estimate update"""

        if not self.company.ibpt_api:
            return

        self.nbs_115069000.action_ibpt_inquiry()
        self.assertTrue(self.nbs_115069000.tax_estimate_ids)

        self.nbs_124043300.action_ibpt_inquiry()
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("nbs_id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        ).unlink()

    def test_nbs_count_product_template(self):
        """Check product template relation with NBS"""

        if not self.company.ibpt_api:
            return

        self.assertEqual(self.nbs_115069000.product_tmpl_qty, 2)
        self.assertEqual(self.nbs_124043300.product_tmpl_qty, 1)

    def test_update_scheduled(self):
        """Check NBS update scheduled"""

        if not self.company.ibpt_api:
            return

        nbss = self.nbs_model.search(
            [("id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        )
        nbss._scheduled_update()

        self.assertTrue(self.nbs_115069000.tax_estimate_ids)
        self.assertTrue(self.nbs_124043300.tax_estimate_ids)

        self.tax_estimate_model.search(
            [("nbs_id", "in", (self.nbs_115069000.id, self.nbs_124043300.id))]
        ).unlink()
