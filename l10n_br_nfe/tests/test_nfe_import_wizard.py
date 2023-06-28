import base64
import os
import re

from odoo.exceptions import UserError
from odoo.tests import SavepointCase

from odoo.addons import l10n_br_nfe


class NFeImportWizardTest(SavepointCase):
    def setUp(self):
        super(NFeImportWizardTest, self).setUp()

        def test_xml_path(filename):
            return os.path.join(
                l10n_br_nfe.__path__[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                filename,
            )

        path_1 = test_xml_path("NFe35200159594315000157550010000000012062777161.xml")
        with open(path_1, "rb") as f:
            self.xml_1 = f.read()

        path_2 = test_xml_path("NFe35200181583054000129550010000000052062777166.xml")
        with open(path_2, "rb") as f:
            self.xml_2 = f.read()

        self.wizard = False
        self.product_1 = self.env["product.product"].create({"name": "Product Test 1"})
        self.partner_1 = self.env["res.partner"].create({"name": "Partner Test 1"})

    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_nfe.import_xml"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "importing_type": "xml_file",
                "xml": base64.b64encode(xml),
            }
        )
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

    def check_edoc(self, edoc):
        self.assertEqual(
            len(self.wizard.imported_products_ids),
            len(edoc.fiscal_line_ids),
        )
        self.assertTrue(edoc.partner_id)
        self.assertEqual(
            self.wizard.xml_partner_cpf_cnpj,
            edoc.partner_id.cnpj_cpf,
        )
        self.assertEqual(
            self.wizard.xml_partner_name,
            edoc.partner_id.name,
        )

    def test_import_xml(self):
        self._prepare_wizard(self.xml_2)
        self.wizard.import_xml()

        self.check_edoc(self.wizard.document_id)

    def test_create_edoc_from_xml(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.purchase_link_type = "create"

        edoc = self.wizard.create_edoc_from_xml()
        self.check_edoc(edoc)
        self.assertIn(self.wizard.purchase_id, edoc.linked_purchase_ids)

    def test_set_fiscal_operation_type(self):
        self._prepare_wizard(self.xml_1)
        doc = self.wizard.get_document_by_xml(False)
        self.assertIsNone(doc)

        doc = self.wizard.get_document_by_xml(self.wizard.parse_xml())
        origin_company = self.wizard.company_id

        doc_company_id = self.env["res.company"].search(
            [("nfe40_CNPJ", "=", re.sub("[^0-9]", "", doc.cnpj_cpf_emitente))], limit=1
        )
        self.wizard.company_id = doc_company_id
        self.wizard.set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "out")

        self.wizard.company_id = origin_company
        self.wizard.set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "in")

    def test_imported_products(self):
        self._prepare_wizard(self.xml_2)
        self.wizard.import_xml()
        first_product = self.wizard.imported_products_ids[0]
        old_product_id = first_product.product_id

        first_product.onchange_product_id()
        first_product.product_id = self.product_1
        with self.assertRaises(UserError):
            first_product.onchange_product_id()

        first_product.product_id = old_product_id
        self.assertNotEqual(first_product.product_id, self.product_1)

        self.supplier_info = self.env["product.supplierinfo"].create(
            {
                "product_id": self.product_1.id,
                "name": self.partner_1.id,
                "partner_uom": self.env["uom.uom"].search([], limit=1).id,
                "price": 100,
            }
        )
        self.wizard.partner_id = self.partner_1
        first_product.product_code = False
        first_product.product_name = False

        first_product._set_product_supplierinfo_data()
        self.assertEqual(first_product.product_id, self.supplier_info.product_id)
        self.assertEqual(first_product.uom_internal, self.supplier_info.partner_uom)

        first_product._create_or_update_product_supplierinfo(self.partner_1)
        self.assertEqual(self.supplier_info.product_id, first_product.product_id)
        self.assertEqual(self.supplier_info.partner_uom, first_product.uom_internal)
        self.assertEqual(self.supplier_info.product_code, first_product.product_code)

    def test_import_xml_purchase(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.purchase_link_type = "create"
        self.wizard.import_xml()

        purchase_id = self.wizard.purchase_id
        self.assertTrue(purchase_id)
        self.assertEqual(
            len(purchase_id.order_line), len(self.wizard.imported_products_ids)
        )
        self.assertEqual(purchase_id.partner_id, self.wizard.partner_id)
