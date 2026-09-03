import base64
import os
import re
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_nfe

from ..wizards.document_import_wizard import DocumentImportWizard


class NFeImportWizardTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def test_xml_path(filename):
            return os.path.join(
                l10n_br_nfe.__path__[0],
                "tests",
                "nfe",
                "v4_00",
                "leiauteNFe",
                filename,
            )

        path_1 = test_xml_path("NFe35200181583054000129550010000000052062777166.xml")
        with open(path_1, "rb") as f:
            cls.xml_1 = f.read()

        cls.wizard = False
        cls.product_1 = cls.env["product.product"].create({"name": "Product Test 1"})
        cls.partner_1 = cls.env["res.partner"].create({"name": "Partner Test 1"})

    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(xml),
            }
        )
        self.wizard._onchange_file()

    def check_edoc(self, edoc):
        self.assertEqual(
            len(self.wizard.imported_products_ids),
            len(edoc.fiscal_line_ids),
        )
        self.assertTrue(edoc.partner_id)
        self.assertEqual(
            self.wizard.issuer_partner_id.vat,
            edoc.partner_id.vat,
        )
        self.assertEqual(
            self.wizard.issuer_partner_id.name,
            edoc.partner_id.name,
        )

    def test_import_nfe_xml(self):
        xml = "dummy"
        with self.assertRaises(ValueError):
            self._prepare_wizard(xml.encode("utf-8"))

        mock_document = MagicMock(spec=["modelo_documento"])
        mock_document.modelo_documento = "65"
        with (
            patch.object(
                DocumentImportWizard,
                "_extract_binding_data",
                return_value=mock_document,
            ),
            self.assertRaises(TypeError),
        ):
            self.wizard._check_xml_data(self.wizard._parse_file())

        self._prepare_wizard(self.xml_1)
        self.wizard._import_edoc()

        self.check_edoc(self.wizard.document_id)

        first_imported_product = self.wizard.imported_products_ids[0]

        self.assertEqual(
            self.wizard.document_key,
            "3520 0181 5830 5400 0129 5500 1000 0000 0520 6277 7166",
        )
        self.assertEqual(self.wizard.document_number, "5")
        self.assertEqual(self.wizard.document_serie, "1")
        self.assertEqual(self.wizard.issuer_partner_id.vat, "81.583.054/0001-29")
        self.assertEqual(self.wizard.issuer_partner_id.name, "Empresa Lucro Presumido")
        self.assertEqual(
            self.wizard.partner_id,
            self.env.ref("l10n_br_base.lucro_presumido_partner"),
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

    def test_create_edoc_from_xml(self):
        self._prepare_wizard(self.xml_1)

        self.wizard.partner_id = False
        binding, edoc = self.wizard._create_edoc_from_file()
        self.assertEqual(self.wizard.partner_id, edoc.partner_id)

        self.check_edoc(edoc)

    def FIXME_test_set_fiscal_operation_type(self):
        self._prepare_wizard(self.xml_1)

        doc = self.wizard._document_key_from_binding(self.wizard._parse_file())
        origin_company = self.wizard.company_id

        doc_company_id = self.env["res.company"].search(
            [("cnpj_cpf_stripped", "=", re.sub("[^0-9]", "", doc.cnpj_cpf_emitente))],
            limit=1,
        )
        self.wizard.company_id = doc_company_id
        self.wizard._set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "out")

        self.wizard.company_id = origin_company
        self.wizard._set_fiscal_operation_type()
        self.assertEqual(self.wizard.fiscal_operation_type, "in")

    def test_imported_products(self):
        self._prepare_wizard(self.xml_1)
        self.wizard._import_edoc()
        first_product = self.wizard.imported_products_ids[0]
        old_product_id = first_product.product_id

        first_product.product_id = False
        first_product.product_name = False
        first_product.product_code = "???"
        first_product.product_supplier_id = False
        first_product._find_or_create_product_supplierinfo()
        self.assertFalse(first_product.product_supplier_id)

        first_product.product_id = old_product_id
        self.assertNotEqual(first_product.product_id, self.product_1)

        self.wizard.partner_id = self.partner_1
        first_product.product_supplier_id = self.env["product.supplierinfo"].create(
            {
                "product_id": self.product_1.id,
                "partner_id": self.partner_1.id,
                "partner_uom_id": self.env["uom.uom"].search([], limit=1).id,
                "price": 100,
            }
        )
        wiz_supplier_id = first_product.product_supplier_id

        first_product._find_or_create_product_supplierinfo()
        self.assertEqual(wiz_supplier_id.product_id, first_product.product_id)
        self.assertEqual(wiz_supplier_id.partner_uom_id, first_product.uom_internal)
        self.assertEqual(wiz_supplier_id.product_name, first_product.product_name)

    def test_match_xml_product(self):
        self._prepare_wizard(self.xml_1)

        xml = self.wizard._parse_file()
        xml_product_1 = xml.infNFe.det[0].prod
        prod_id = self.wizard._match_product(xml_product_1)
        self.assertEqual(prod_id, self.env.ref("product.product_product_10"))

        prod_code = self.env["product.product"].create(
            {
                "name": "TEST1",
                "default_code": "TEST123",
            }
        )

        mock_code = MagicMock(spec=["cProd"])
        mock_code.cProd = "TEST123"
        prod_id = self.wizard._match_product(mock_code)

        mock_code = MagicMock(spec=["cProd"])
        mock_code.cProd = "TEST123"
        prod_id = self.wizard._match_product(mock_code)
        self.assertEqual(prod_id, prod_code)

        prod_code.unlink()
        prod_barcode = self.env["product.product"].create(
            {"name": "TEST2", "barcode": "123456789123"}
        )
        mock_barcode = MagicMock(spec=["cEANTrib"])
        mock_barcode.cProd = False
        mock_barcode.cEANTrib = "123456789123"
        prod_id = self.wizard._match_product(mock_barcode)
        self.assertEqual(prod_id, prod_barcode)

        prod_barcode.unlink()
        prod_id = self.wizard._match_product(MagicMock())
        self.assertFalse(prod_id)

    def test_match_product_by_purchase(self):
        """xPed/nItemPed map to the buyer's purchase.order.name and
        purchase.order.line.sequence. When purchase is absent it must no-op,
        so _match_product falls back to supplierinfo/default_code/barcode."""
        self._prepare_wizard(self.xml_1)
        pol_model = self.env.get("purchase.order.line")

        mock = MagicMock()
        mock.xPed = "NONEXISTENT-PO-REF"
        mock.nItemPed = "999"
        # No PO references this xPed (and/or purchase absent) -> no match,
        # and crucially no crash on a missing model.
        self.assertFalse(self.wizard._match_product_by_purchase(mock))

        if pol_model is None:
            # guard short-circuits before any purchase.order.line search
            self.assertFalse(
                self.wizard._match_product_by_purchase(
                    self.wizard._parse_file().infNFe.det[0].prod
                )
            )
            return

        # xPed = purchase.order.name, nItemPed = line sequence.
        partner = self.env["res.partner"].create({"name": "Vendor PO"})
        product = self.env["product.product"].create({"name": "PO Product"})
        order = self.env["purchase.order"].create({"partner_id": partner.id})
        line = self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "name": "PO Product",
                "product_qty": 1.0,
                "price_unit": 10.0,
                "date_planned": fields.Datetime.now(),
            }
        )
        self.wizard.partner_id = partner
        mock = MagicMock()
        mock.xPed = order.name
        mock.nItemPed = str(line.sequence)
        self.assertEqual(self.wizard._match_product_by_purchase(mock), product)

    def test_product_domain_restricted_to_purchase_lines(self):
        """An unmatched product line proposes only the products ordered from
        the NFe supplier on a confirmed purchase order with quantity still to
        be billed (parity with the legacy akretion importer restriction)."""
        self._prepare_wizard(self.xml_1)
        pol_model = self.env.get("purchase.order.line")
        if pol_model is None:
            self.skipTest("purchase module not installed")

        supplier = self.env["res.partner"].create({"name": "Vendor Domain"})
        ordered = self.env["product.product"].create(
            {"name": "Ordered Product", "purchase_ok": True}
        )
        other = self.env["product.product"].create(
            {"name": "Other Product", "purchase_ok": True}
        )
        billed = self.env["product.product"].create(
            {"name": "Billed Product", "purchase_ok": True}
        )
        # Bill on ordered quantities so an unreceived line still has
        # qty_to_invoice > 0 (the Odoo 16 default is 'receive', where
        # qty_to_invoice = qty_received - qty_invoiced = 0 before receipt).
        for product in (ordered, other, billed):
            product.purchase_method = "purchase"

        # confirmed PO with an outstanding line -> candidate
        order = self.env["purchase.order"].create({"partner_id": supplier.id})
        self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "product_id": ordered.id,
                "name": "Ordered Product",
                "product_qty": 1.0,
                "price_unit": 10.0,
                "date_planned": fields.Datetime.now(),
            }
        )
        order.button_confirm()

        # fully billed line on the same confirmed PO -> not a candidate
        billed_line = self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "product_id": billed.id,
                "name": "Billed Product",
                "product_qty": 1.0,
                "price_unit": 10.0,
                "date_planned": fields.Datetime.now(),
            }
        )
        billed_line.write({"qty_to_invoice": 0.0})

        # draft PO line -> not a candidate either (core zeroes qty_to_invoice)
        draft_order = self.env["purchase.order"].create({"partner_id": supplier.id})
        self.env["purchase.order.line"].create(
            {
                "order_id": draft_order.id,
                "product_id": other.id,
                "name": "Other Product",
                "product_qty": 1.0,
                "price_unit": 10.0,
                "date_planned": fields.Datetime.now(),
            }
        )

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "partner_id": supplier.id,
            }
        )
        line = self.env["l10n_br_fiscal.document.import.wizard.line"].create(
            {"import_xml_id": wizard.id}
        )

        # unmatched product -> restricted to the open PO-line product only
        domain = line.product_domain
        candidate_ids = [pid for leaf in domain if leaf[0] == "id" for pid in leaf[2]]
        self.assertEqual(candidate_ids, [ordered.id])
        self.assertNotIn(billed.id, candidate_ids)
        self.assertNotIn(other.id, candidate_ids)

        # once matched, the restriction relaxes so the user can adjust freely
        line.product_id = ordered
        self.assertEqual(line.product_domain, [["purchase_ok", "=", True]])

        # a supplier without any open PO line is not restricted either
        no_po_vendor = self.env["res.partner"].create({"name": "No PO Vendor"})
        other_wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "partner_id": no_po_vendor.id,
            }
        )
        line2 = self.env["l10n_br_fiscal.document.import.wizard.line"].create(
            {"import_xml_id": other_wizard.id}
        )
        self.assertEqual(line2.product_domain, [["purchase_ok", "=", True]])

    def test__parse_xml(self):
        self._prepare_wizard(self.xml_1)

        first_product = self.wizard.imported_products_ids[0]
        first_product.new_cfop_id = self.env.ref("l10n_br_fiscal.cfop_5111").id

        xml = self.wizard._parse_file()
        first_xml_product = xml.infNFe.det[0].prod
        self.assertEqual(first_xml_product.CFOP, "5111")

        mock_prod = MagicMock(spec=["imposto"])
        mock_prod.imposto.ICMS.ICMS60.pICMS = 60
        mock_prod.imposto.ICMS.ICMS60.vICMS = 100
        mock_prod.imposto.IPI.IPITrib.pIPI = 5
        mock_prod.imposto.IPI.IPITrib.vIPI = 100
        taxes = self.wizard._get_taxes_from_xml_product(mock_prod)

        self.assertEqual(taxes["pICMS"], 60)
        self.assertEqual(taxes["vICMS"], 100)
        self.assertEqual(taxes["pIPI"], 5)
        self.assertEqual(taxes["vIPI"], 100)

    def test_cfop_warning(self):
        """The wizard line flags a CFOP whose scope (intra/interstate) is
        inconsistent with the real issuer/company geography."""
        sp = self.env.ref("base.state_br_sp")
        rj = self.env.ref("base.state_br_rj")
        company = self.env.ref("base.main_company")
        company.state_id = sp
        issuer = self.env["res.partner"].create(
            {"name": "Issuer SP", "state_id": sp.id}
        )
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {"company_id": company.id, "issuer_partner_id": issuer.id}
        )
        line = self.env["l10n_br_fiscal.document.import.wizard.line"].create(
            {"import_xml_id": wizard.id}
        )

        # interstate CFOP but both parties in SP -> warn
        line.cfop_xml = "6101"
        self.assertTrue(line.cfop_warning)

        # intrastate CFOP and both parties in SP -> no warning
        line.cfop_xml = "1101"
        self.assertFalse(line.cfop_warning)

        # issuer now in RJ: intrastate CFOP is inconsistent -> warn
        issuer.state_id = rj
        line._compute_cfop_warning()
        self.assertTrue(line.cfop_warning)

        # interstate CFOP with issuer RJ / company SP -> consistent, no warning
        line.cfop_xml = "6101"
        line._compute_cfop_warning()
        self.assertFalse(line.cfop_warning)
