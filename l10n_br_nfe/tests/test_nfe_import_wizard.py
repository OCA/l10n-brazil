import base64
import os

from odoo.tests import SavepointCase

from odoo.addons import l10n_br_nfe


class NFeImportWizardTest(SavepointCase):
    def setUp(self):
        super(NFeImportWizardTest, self).setUp()

        def test_xml_path(path):
            return os.path.join(
                l10n_br_nfe.__path__[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                path,
            )

        path_1 = test_xml_path("NFe35200159594315000157550010000000012062777161.xml")
        with open(path_1, "rb") as f:
            self.xml_1 = f.read()

        path_2 = test_xml_path("NFe35200181583054000129550010000000052062777166.xml")
        with open(path_2, "rb") as f:
            self.xml_2 = f.read()

        self.wizard = self.env["l10n_br_nfe.import_xml"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "importing_type": "xml_file",
            }
        )

    def _prepare_wizard(self, xml):
        self.wizard.xml = base64.b64encode(xml)
        self.wizard._onchange_xml()

    def test_onchange_nfe_xml(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.import_xml()

        first_imported_product = self.wizard.imported_products_ids[0]

        self.assertEqual(
            self.wizard.document_key, "35200159594315000157550010000000012062777161"
        )
        self.assertEqual(self.wizard.document_number, "1")
        self.assertEqual(self.wizard.document_serie, "1")
        self.assertEqual(self.wizard.xml_partner_cpf_cnpj, "59.594.315/0001-57")
        self.assertEqual(self.wizard.xml_partner_name, "TESTE - Simples Nacional")
        self.assertEqual(
            self.wizard.partner_id,
            self.env.ref("l10n_br_base.simples_nacional_partner"),
        )
        self.assertEqual(
            f"[{first_imported_product.product_code}] "
            f"{first_imported_product.product_name}",
            "[E-COM11] Cabinet with Doors",
        )
        self.assertEqual(first_imported_product.uom_com, "UNID")
        self.assertEqual(first_imported_product.quantity_com, 1)
        self.assertEqual(first_imported_product.price_unit_com, 14)
        self.assertEqual(first_imported_product.uom_trib, "UNID")
        self.assertEqual(first_imported_product.quantity_trib, 1)
        self.assertEqual(first_imported_product.price_unit_trib, 14)
        self.assertEqual(first_imported_product.total, 14)

    def test_import_xml(self):
        self._prepare_wizard(self.xml_2)
        self.wizard.imported_products_ids.product_id = self.env.ref(
            "product.product_product_5"
        )
        self.wizard.import_xml()

        edoc = self.wizard.document_id
        self.assertEqual(
            self.wizard.imported_products_ids.product_id,
            edoc.fiscal_line_ids.product_id,
        )
        self.assertEqual(
            self.wizard.imported_products_ids.product_id.ncm_id,
            edoc.fiscal_line_ids.ncm_id,
        )
        self.assertTrue(edoc.partner_id.country_id)
        self.assertTrue(edoc.partner_id.state_id)
        self.assertTrue(edoc.partner_id.city_id)
