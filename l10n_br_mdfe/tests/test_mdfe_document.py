# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from nfelib.nfe.ws.edoc_legacy import MDFeAdapter

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class MDFeDocumentTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        FiscalDocument = cls.env["l10n_br_fiscal.document"]

        cls.acre_state = cls.env.ref("base.state_br_ac")
        cls.mdfe_document_type_id = cls.env.ref("l10n_br_fiscal.document_58")
        cls.sn_company_id = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.sn_company_id.processador_edoc = "erpbrasil.edoc"
        cls.mdfe_id = FiscalDocument.create(
            {
                "document_type_id": cls.mdfe_document_type_id.id,
                "company_id": cls.sn_company_id.id,
                "document_number": "70000",
                "document_serie": "30",
                "document_data": datetime.now(),
            }
        )

    def test_mdfe_compute_fields(self):
        self.mdfe_id.fiscal_additional_data = "TEST FISCAL ADDITIONAL DATA"
        self.mdfe_id.customer_additional_data = "TEST CUSTOMER ADDITIONAL DATA"

        self.assertTrue(self.mdfe_id.mdfe30_infAdFisco)
        self.assertTrue(self.mdfe_id.mdfe30_infCpl)

    def test_mdfe_inverse_fields(self):
        self.mdfe_id.mdfe30_UFIni = self.acre_state.code
        self.mdfe_id.mdfe30_UFFim = self.acre_state.code
        self.assertEqual(self.mdfe_id.mdfe_initial_state_id, self.acre_state)
        self.assertEqual(self.mdfe_id.mdfe_final_state_id, self.acre_state)

        self.mdfe_id.mdfe30_UF = self.acre_state.ibge_code
        self.assertEqual(self.mdfe_id.company_id.partner_id.state_id, self.acre_state)

        self.mdfe_id.mdfe30_infMunCarrega = [
            (
                0,
                0,
                {
                    "mdfe30_cMunCarrega": "1200013",
                    "mdfe30_xMunCarrega": "Acrelândia",
                },
            )
        ]
        self.assertIn(
            self.env.ref("l10n_br_base.city_1200013"),
            self.mdfe_id.mdfe_loading_city_ids,
        )

    def test_mdfe_processor(self):
        processor = self.mdfe_id._edoc_processor()
        self.assertTrue(isinstance(processor, MDFeAdapter))

        self.mdfe_id.document_type_id = False
        processor = self.mdfe_id._edoc_processor()
        self.assertFalse(isinstance(processor, MDFeAdapter))

        self.mdfe_id.document_type_id = self.mdfe_document_type_id

        self.mdfe_id.company_id.certificate_nfe_id = False
        processor = self.mdfe_id._edoc_processor()
        self.assertTrue(isinstance(processor, MDFeAdapter))

        self.mdfe_id.company_id.certificate_ecnpj_id = False
        with self.assertRaises(UserError):
            processor = self.mdfe_id._edoc_processor()

    def test_generate_key(self):
        self.mdfe_id._generate_key()
        self.assertTrue(self.mdfe_id.document_key)
        self.assertTrue(self.mdfe_id.key_random_code)
        self.assertTrue(self.mdfe_id.key_check_digit)
