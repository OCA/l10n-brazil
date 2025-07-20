# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Basic setup for the test
        cls.partner_model = cls.env["res.partner"]
        cls.partner = cls.partner_model.create(
            {
                "name": "Test Partner",
                "cnpj_cpf": "87697453000105",
                "zip": "12345000",
                "phone": "(11) 91234-5678",
                "email": "test@company.com",
                "country_id": cls.env.ref("base.br").id,
                "is_company": True,
            }
        )

    def test_compute_cte40_xEnder(self):
        """Test the computation of the field cte40_xEnder"""
        self.partner.write(
            {
                "street": "Test Street",
                "street2": "Apt 101",
                "district": "Downtown",
            }
        )
        self.partner._compute_cte40_xEnder()
        self.assertEqual(
            self.partner.cte40_xEnder,
            "Test Street - Apt 101 - Downtown",
            "The cte40_xEnder field was not computed correctly",
        )

    def test_compute_cte_data(self):
        """Test the computation of fields related to CNPJ/CPF"""
        self.partner._compute_cte_data()
        self.assertEqual(
            self.partner.cte40_CNPJ, "87697453000105", "CNPJ was not computed correctly"
        )
        self.assertFalse(self.partner.cte40_CPF, "CPF should not be set for companies")

    def test_inverse_cte40_CNPJ(self):
        """Test the inverse method for the CNPJ field"""
        self.partner.cte40_CNPJ = "21524956000162"
        self.partner._inverse_cte40_CNPJ()
        self.assertEqual(
            self.partner.cnpj_cpf,
            "21.524.956/0001-62",
            "CNPJ was not formatted correctly",
        )

    def test_inverse_cte40_CEP(self):
        """Test the inverse method for the ZIP code"""
        self.partner.cte40_CEP = "12345999"
        self.partner._inverse_cte40_CEP()
        self.assertEqual(
            self.partner.zip, "12345-999", "ZIP code was not formatted correctly"
        )

    def test_match_or_create_m2o(self):
        """Test the match_or_create_m2o method"""
        parent_dict = {"cte40_CNPJ": "87697453000105"}
        rec_dict = {}
        result_id = self.partner_model.match_or_create_m2o(rec_dict, parent_dict)
        self.assertTrue(result_id, "Could not create or find a Many2One record")
