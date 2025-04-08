import base64
import os

from odoo.exceptions import UserError
from odoo.tests import SavepointCase

from odoo.addons.l10n_br_nfe import __path__ as nfe_path


class NFeImportWizardTest(SavepointCase):
    def setUp(self):
        super().setUp()

        def test_xml_path(filename):
            return os.path.join(
                nfe_path[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                filename,
            )

        path_1 = test_xml_path("NFe35200181583054000129550010000000052062777166.xml")
        with open(path_1, "rb") as f:
            self.xml_1 = f.read()
        path_2 = test_xml_path("NFe35200181583054000129550010000000052062771230.xml")
        with open(path_2, "rb") as f:
            self.xml_2 = f.read()

        self.wizard = False
        self.partner_1 = self.env["res.partner"].create({"name": "Partner Test 1"})

    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(xml),
            }
        )
        self.wizard._onchange_file()

    def test_import_nfe_product_not_found(self):
        """To avoid false positives in test_import_nfe_xml, we need to ensure
        that the product is not found in the database. This is done by changing
        the name and default_code of the product to something else."""

        # Alter matching information from product (to avoid matching)
        tmpl1_id = self.env.ref("product.product_product_10_product_template")
        prod1_id = tmpl1_id.product_variant_id
        prod1_id.name = "Test Product"
        prod1_id.default_code = "TEST123"

        self._prepare_wizard(self.xml_1)
        binding, edoc = self.wizard._import_edoc()

        self.assertEqual(edoc.fiscal_line_ids.product_id.id, False)

    def test_import_nfe_xml(self):
        # Test invalid XML
        with self.assertRaises(UserError):
            self._prepare_wizard(b"invalid_xml")

        # Test valid XML
        self._prepare_wizard(self.xml_1)
        binding, edoc = self.wizard._import_edoc()

        self.assertTrue(edoc)
        self.assertEqual(
            edoc.document_key, "35200181583054000129550010000000052062777166"
        )
        self.assertEqual(edoc.partner_id.cnpj_cpf, "81.583.054/0001-29")
        self.assertEqual(edoc.partner_id.name, "Empresa Lucro Presumido")

        # Check if product was recognized
        tmpl1_id = self.env.ref("product.product_product_10_product_template")
        prod1_id = tmpl1_id.product_variant_id
        self.assertEqual(edoc.fiscal_line_ids.product_id, prod1_id)

        # Open a new l10n_br_fiscal.document.line.import.wizard for doc line
        document_line = edoc.fiscal_line_ids[0]
        wizard = (
            self.env["l10n_br_fiscal.document.line.import.wizard"]
            .with_context(active_id=document_line.id)
            .create({})
        )

        # Fill in required fields (uom_id, quantity)
        wizard.import_qty = 1
        wizard.update(wizard._prepare_onchange_document_line_id())
        wizard.flush()

        # Confirm the wizard
        wizard.action_done()

        # Assert that the product has a new product.supplierinfo with the correct values
        supplierinfo = self.env["product.supplierinfo"].search(
            [
                ("name", "=", edoc.partner_id.id),
                ("product_id", "=", prod1_id.id),
                ("product_code", "=", wizard.document_code),
            ],
            limit=1,
        )
        self.assertTrue(supplierinfo)
        self.assertEqual(supplierinfo.product_code, wizard.document_code)
        self.assertEqual(supplierinfo.partner_uom, wizard.document_uom)
        self.assertEqual(supplierinfo.partner_uom_factor, 1)

    def test_import_nfe_with_new_uom(self):
        self._prepare_wizard(self.xml_2)
        binding, edoc = self.wizard._import_edoc()

        # Check if product was recognized
        tmpl1_id = self.env.ref("product.product_product_10_product_template")
        prod1_id = tmpl1_id.product_variant_id
        self.assertEqual(edoc.fiscal_line_ids.product_id, prod1_id)

        # Qauntity and UoM should be empty
        uom_id = edoc.fiscal_line_ids.uom_id
        self.assertEqual(uom_id.id, False)
        quantity = edoc.fiscal_line_ids.quantity
        self.assertEqual(quantity, 0)

    def test_import_nfe_with_existing_uom(self):
        # Create new test product.supplier.info
        tmpl1_id = self.env.ref("product.product_product_10_product_template")
        prod1_id = tmpl1_id.product_variant_id
        prod1_id.seller_ids = self.env["product.supplierinfo"].create(
            {
                "name": self.partner_1.id,
                "product_code": "E-COM11",
                "product_name": "Cabinet with Doors",
                "product_id": prod1_id.id,
                "partner_uom": "U",
                "partner_uom_factor": 1,
            }
        )

        self._prepare_wizard(self.xml_2)
        binding, edoc = self.wizard._import_edoc()

        # Check if product was recognized
        self.assertEqual(edoc.fiscal_line_ids.product_id, prod1_id)

        # Qauntity and UoM should be matched
        uom_id = edoc.fiscal_line_ids.uom_id
        self.assertEqual(uom_id, prod1_id.uom_id)
        quantity = edoc.fiscal_line_ids.quantity
        self.assertEqual(quantity, 10)

    def test_fiscal_operation_type(self):
        self._prepare_wizard(self.xml_1)
        self.wizard._compute_fiscal_operation_type()

        if self.wizard.issuer_cnpj == self.wizard.company_id.cnpj_cpf:
            self.assertEqual(self.wizard.fiscal_operation_type, "out")
        else:
            self.assertEqual(self.wizard.fiscal_operation_type, "in")

    def test_destination_partner_detection(self):
        self._prepare_wizard(self.xml_1)
        self.wizard._destination_partner_from_binding(self.wizard._parse_file())

        self.assertEqual(
            self.wizard.destination_partner_id.cnpj_cpf, "81.493.979/0001-89"
        )
        partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        self.assertEqual(self.wizard.destination_partner_id.name, partner_id.name)
