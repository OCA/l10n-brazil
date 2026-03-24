# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.tests import TransactionCase


class CTeDocumentTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        FiscalDocument = cls.env["l10n_br_fiscal.document"]

        cls.acre_state = cls.env.ref("base.state_br_ac")
        cls.cte_document_type_id = cls.env.ref("l10n_br_fiscal.document_57")
        cls.sn_company_id = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.sn_company_id.processador_edoc = "oca"
        cls.cte_id = FiscalDocument.create(
            {
                "document_type_id": cls.cte_document_type_id.id,
                "company_id": cls.sn_company_id.id,
                "document_number": "70000",
                "document_serie": "30",
                "document_date": datetime.now(),
            }
        )

    # TODO: Tratar
    # def test_cte_compute_fields(self):
    #     self.cte_id.fiscal_additional_data = "TEST FISCAL ADDITIONAL DATA"
    #     self.cte_id.customer_additional_data = "TEST CUSTOMER ADDITIONAL DATA"

    #     self.assertTrue(self.cte_id.cte40_infAdFisco)
    #     self.assertTrue(self.cte_id.cte40_infCpl)

    # TODO: Tratar
    # def test_cte_inverse_fields(self):
    #     self.cte_id.cte40_UFIni = self.acre_state.code
    #     self.cte_id.cte40_UFFim = self.acre_state.code
    #     self.assertEqual(self.cte_id.cte_initial_state_id, self.acre_state)
    #     self.assertEqual(self.cte_id.cte_final_state_id, self.acre_state)

    #     self.cte_id.cte40_UF = self.acre_state.ibge_code
    #     self.assertEqual(self.cte_id.company_id.partner_id.state_id, self.acre_state)

    #     self.cte_id.cte40_infMunCarrega = [
    #         (
    #             0,
    #             0,
    #             {
    #                 "cte40_cMunCarrega": "1200013",
    #                 "cte40_xMunCarrega": "Acrelândia",
    #             },
    #         )
    #     ]
    #     self.assertIn(
    #         self.env.ref("l10n_br_base.city_1200013"),
    #         self.cte_id.cte_loading_city_ids,
    #     )

    # def test_cte_processor(self):
    #     processor = self.cte_id._edoc_processor()
    #     self.assertTrue(isinstance(processor, CTeAdapter))

    #     self.cte_id.document_type_id = False
    #     processor = self.cte_id._edoc_processor()
    #     self.assertFalse(isinstance(processor, CTeAdapter))

    #     self.cte_id.document_type_id = self.cte_document_type_id

    #     self.cte_id.company_id.certificate_nfe_id = False
    #     with self.assertRaises(UserError):
    #         processor = self.cte_id._edoc_processor()

    def test_generate_key(self):
        self.cte_id._generate_key()
        self.assertTrue(self.cte_id.document_key)
        self.assertTrue(self.cte_id.key_random_code)
        self.assertTrue(self.cte_id.key_check_digit)
