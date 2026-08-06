# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from unittest import mock

from nfelib.nfe.ws.edoc_legacy import MDFeAdapter

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class MDFeDocumentTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        FiscalDocument = cls.env["l10n_br_fiscal.document"]

        cls.mg_state = cls.env.ref("base.state_br_mg")
        cls.mdfe_document_type_id = cls.env.ref("l10n_br_fiscal.document_58")
        cls.sn_company_id = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.sn_company_id.processador_edoc = "oca"
        cls.mdfe_id = FiscalDocument.create(
            {
                "document_type_id": cls.mdfe_document_type_id.id,
                "company_id": cls.sn_company_id.id,
                "document_number": "70000",
                "document_serie": "30",
                "document_date": datetime.now(),
            }
        )

    def test_mdfe_compute_fields(self):
        self.mdfe_id.fiscal_additional_data = "TEST FISCAL ADDITIONAL DATA"
        self.mdfe_id.customer_additional_data = "TEST CUSTOMER ADDITIONAL DATA"

        self.assertTrue(self.mdfe_id.mdfe30_infAdFisco)
        self.assertTrue(self.mdfe_id.mdfe30_infCpl)

    def test_mdfe_inverse_fields(self):
        self.mdfe_id.mdfe30_UFIni = self.mg_state.code
        self.mdfe_id.mdfe30_UFFim = self.mg_state.code
        self.assertEqual(self.mdfe_id.mdfe_initial_state_id, self.mg_state)
        self.assertEqual(self.mdfe_id.mdfe_final_state_id, self.mg_state)

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
        self.mdfe_id.company_id.invalidate_cache()
        with self.assertRaises(ValidationError):
            processor = self.mdfe_id._edoc_processor()

    def test_generate_key(self):
        self.mdfe_id._generate_key()
        self.assertTrue(self.mdfe_id.document_key)
        self.assertTrue(self.mdfe_id.key_random_code)
        self.assertTrue(self.mdfe_id.key_check_digit)

    def _create_company(self, name):
        return self.env["res.company"].create({"name": name})

    def _create_mdfe_document(self, company, number=False, serie=False):
        return self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.mdfe_document_type_id.id,
                "company_id": company.id,
                "issuer": "company",
                "document_number": number,
                "document_serie": serie,
                "document_date": datetime.now(),
            }
        )

    def test_generate_key_company_without_cnpj(self):
        company = self._create_company("Company Without CNPJ")
        document = self._create_mdfe_document(company)
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_company_without_state(self):
        company = self._create_company("Company Without State")
        company.partner_id.vat = "12.345.678/0001-95"
        document = self._create_mdfe_document(company)
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_without_number(self):
        # main_company has vat/state but no MDF-e serie
        company = self.env.ref("base.main_company")
        document = self._create_mdfe_document(company)
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_without_serie(self):
        company = self.env.ref("base.main_company")
        document = self._create_mdfe_document(company, number="90201")
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_does_not_fill_serie(self):
        # Even with document_serie_id set, _generate_key must not fill the
        # serie: that is the responsibility of _document_number, called before
        # _generate_key in the standard workflow.
        document = self._create_mdfe_document(
            self.sn_company_id, number="90202", serie="30"
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_serie = '' WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["document_serie"])
        with self.assertRaises(ValidationError):
            document._generate_key()
        self.assertFalse(document.document_key)

    def test_generate_key_without_transmission(self):
        document = self._create_mdfe_document(
            self.sn_company_id, number="90203", serie="30"
        )
        document.mdfe_transmission = False
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_non_numeric_serie(self):
        document = self._create_mdfe_document(
            self.sn_company_id, number="90204", serie="30"
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_serie = '9A1' "
            "WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["document_serie"])
        with self.assertRaises(ValidationError) as cm:
            document._generate_key()
        self.assertIn("must contain only numbers", str(cm.exception))

    def test_generate_key_other_processor(self):
        document = self._create_mdfe_document(
            self.sn_company_id, number="90205", serie="30"
        )
        with mock.patch(
            "odoo.addons.l10n_br_mdfe.models.document.filtered_processador_edoc_mdfe",
            return_value=False,
        ):
            document._generate_key()
        self.assertTrue(document.document_key)
