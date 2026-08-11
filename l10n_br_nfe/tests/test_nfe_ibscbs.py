# Copyright 2025
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from decimal import Decimal

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNFeIBSCBS(TransactionCase):
    """Test IBSCBS field export and computation in NFe documents"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Get or create company
        cls.company = cls.env.ref("base.main_company")
        if not cls.company.partner_id.state_id:
            # Create a state if needed
            cls.state = cls.env["res.country.state"].create(
                {
                    "name": "Test State",
                    "code": "TS",
                    "country_id": cls.env.ref("base.br").id,
                    "ibge_code": "35",
                }
            )
            cls.company.partner_id.state_id = cls.state

        # Get or create partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "vat": "65910976000147",
            }
        )

        # Get or create product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "list_price": 100.0,
            }
        )

        # Create fiscal document
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )

    def test_export_field_ibscbs_with_ibs_value(self):
        """Test _export_field for IBSCBS with IBS value"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # Write computed fields directly for testing
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.CST, "000")
        self.assertEqual(result.cClassTrib, "000001")
        self.assertIsNotNone(result.gIBSCBS)
        self.assertEqual(result.gIBSCBS.vBC, "100.00")
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "10.00")
        self.assertEqual(result.gIBSCBS.vIBS, "10.00")

    def test_export_field_ibscbs_with_cbs_value(self):
        """Test _export_field for IBSCBS with CBS value"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "cbs_value": 5.0,
                "cbs_percent": 5.0,
                "cbs_base": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_field_ibscbs_with_both_values(self):
        """Test _export_field for IBSCBS with both IBS and CBS values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
                "cbs_value": 5.0,
                "cbs_percent": 5.0,
                "cbs_base": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.gIBSCBS.vIBS, "10.00")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_field_ibscbs_without_values(self):
        """Test _export_field for IBSCBS without IBS or CBS values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertFalse(result)

    def test_export_field_ibscbs_with_tax_classification(self):
        """Test _export_field for IBSCBS with tax classification"""
        # Create tax classification
        tax_classification = self.env["l10n_br_fiscal.tax.classification"].create(
            {
                "name": "Test Classification",
                "code": "123",
            }
        )

        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_classification_id": tax_classification.id,
            }
        )
        line.write({"ibs_value": 10.0})

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.cClassTrib, "000123")

    def test_export_field_ibscbs_with_ibs_cst(self):
        """Test _export_field for IBSCBS with IBS CST"""
        # Get or create IBS tax group
        ibs_tax_group = self.env.ref("l10n_br_fiscal.tax_group_ibs")
        # Create IBS CST
        ibs_cst = self.env["l10n_br_fiscal.cst"].create(
            {
                "name": "IBS CST Test",
                "code": "50",
                "cst_type": "out",
                "tax_group_id": ibs_tax_group.id,
            }
        )

        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "ibs_cst_id": ibs_cst.id,
            }
        )
        line.write({"ibs_value": 10.0})

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.CST, "50")

    def test_export_field_ibscbs_with_cbs_cst(self):
        """Test _export_field for IBSCBS with CBS CST"""
        # Get or create CBS tax group
        cbs_tax_group = self.env.ref("l10n_br_fiscal.tax_group_cbs")
        # Create CBS CST
        cbs_cst = self.env["l10n_br_fiscal.cst"].create(
            {
                "name": "CBS CST Test",
                "code": "60",
                "cst_type": "out",
                "tax_group_id": cbs_tax_group.id,
            }
        )

        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "cbs_cst_id": cbs_cst.id,
            }
        )
        line.write({"cbs_value": 5.0})

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.CST, "60")

    def test_export_field_ibscbs_calculated_ibs_uf(self):
        """Test _export_field for IBSCBS with calculated IBS UF value"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # Need at least a minimal value to pass the initial check
        # Then it will calculate from base and percent
        line.write(
            {
                "ibs_value": 0.01,  # Minimal value to pass check
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        # vIBSUF should use ibs_value directly when available
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "0.01")
        self.assertEqual(result.gIBSCBS.gIBSUF.pIBSUF, "10.0000")

    def test_export_field_ibscbs_calculated_cbs(self):
        """Test _export_field for IBSCBS with calculated CBS value"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # Need at least a minimal value to pass the initial check
        # Then it will calculate from base and percent
        line.write(
            {
                "cbs_value": 0.01,  # Minimal value to pass check
                "cbs_percent": 5.0,
                "cbs_base": 100.0,
            }
        )

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        # vCBS should use cbs_value directly when available
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "0.01")
        self.assertEqual(result.gIBSCBS.gCBS.pCBS, "5.0000")

    def test_export_many2one_ibscbs(self):
        """Test _export_many2one for IBSCBS"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = line._export_many2one("nfe40_IBSCBS", False)
        self.assertIsNotNone(result)
        self.assertEqual(result.CST, "000")
        self.assertIsNotNone(result.gIBSCBS)

    def test_export_many2one_ibscbs_without_values(self):
        """Test _export_many2one for IBSCBS without values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )

        result = line._export_many2one("nfe40_IBSCBS", False)
        self.assertFalse(result)

    def test_export_fields_nfe_40_imposto_with_ibs(self):
        """Test _export_fields_nfe_40_imposto adds IBSCBS to export_dict"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
                "tax_icms_or_issqn": "icms",
            }
        )
        # Force compute of nfe40_choice_imposto
        line._compute_nfe40_choice_imposto()

        # Include all fields that the method may try to remove
        xsd_fields = [
            "nfe40_ICMS",
            "nfe40_ISSQN",
            "nfe40_II",
            "nfe40_ICMSUFDest",
            "nfe40_PISST",
            "nfe40_COFINSST",
            "nfe40_IPI",
            "nfe40_IBSCBS",
        ]
        export_dict = {}
        line._export_fields_nfe_40_imposto(xsd_fields, None, export_dict)

        self.assertIn("IBSCBS", export_dict)
        self.assertIsNotNone(export_dict["IBSCBS"])

    def test_export_fields_nfe_40_imposto_without_ibs_cbs(self):
        """Test _export_fields_nfe_40_imposto removes IBSCBS when no values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "tax_icms_or_issqn": "icms",
            }
        )
        # Force compute of nfe40_choice_imposto
        line._compute_nfe40_choice_imposto()

        # Include all fields that the method may try to remove
        xsd_fields = [
            "nfe40_ICMS",
            "nfe40_ISSQN",
            "nfe40_II",
            "nfe40_ICMSUFDest",
            "nfe40_PISST",
            "nfe40_COFINSST",
            "nfe40_IPI",
            "nfe40_IBSCBS",
        ]
        export_dict = {}
        line._export_fields_nfe_40_imposto(xsd_fields, None, export_dict)

        self.assertNotIn("IBSCBS", export_dict)
        self.assertNotIn("nfe40_IBSCBS", xsd_fields)

    def test_compute_nfe40_ibscbstot_fields_empty(self):
        """Test _compute_nfe40_IBSCBSTot_fields with no lines"""
        self.document.fiscal_line_ids = False
        self.document._compute_nfe40_IBSCBSTot_fields()

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 0.0)
        self.assertEqual(self.document.nfe40_vIBS, 0.0)
        self.assertEqual(self.document.nfe40_vCBS, 0.0)

    def test_compute_nfe40_ibscbstot_fields_with_ibs(self):
        """Test _compute_nfe40_IBSCBSTot_fields with IBS values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        self.document._compute_nfe40_IBSCBSTot_fields()

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 100.0)
        self.assertEqual(self.document.nfe40_vIBS, 10.0)
        self.assertEqual(self.document.nfe40_vIBSUF, 10.0)

    def test_compute_nfe40_ibscbstot_fields_with_cbs(self):
        """Test _compute_nfe40_IBSCBSTot_fields with CBS values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "cbs_value": 5.0,
                "cbs_base": 100.0,
            }
        )

        self.document._compute_nfe40_IBSCBSTot_fields()

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 100.0)
        self.assertEqual(self.document.nfe40_vCBS, 5.0)

    def test_compute_nfe40_ibscbstot_fields_with_multiple_lines(self):
        """Test _compute_nfe40_IBSCBSTot_fields with multiple lines"""
        line1 = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line1.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        line2 = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 200.0,
            }
        )
        line2.write(
            {
                "ibs_value": 20.0,
                "ibs_base": 200.0,
            }
        )

        self.document._compute_nfe40_IBSCBSTot_fields()

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 300.0)
        self.assertEqual(self.document.nfe40_vIBS, 30.0)
        self.assertEqual(self.document.nfe40_vIBSUF, 30.0)

    def test_export_field_ibscbstot_with_values(self):
        """Test _export_field for IBSCBSTot with IBS/CBS values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = self.document._export_field("nfe40_IBSCBSTot", None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.vBCIBSCBS, "100.00")
        self.assertIsNotNone(result.gIBS)
        self.assertEqual(result.gIBS.vIBS, "10.00")
        self.assertIsNotNone(result.gCBS)

    def test_export_field_ibscbstot_without_values(self):
        """Test _export_field for IBSCBSTot without IBS/CBS values"""
        result = self.document._export_field("nfe40_IBSCBSTot", None, None)
        self.assertFalse(result)

    def test_export_many2one_ibscbstot_with_values(self):
        """Test _export_many2one for IBSCBSTot with values"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        # The method checks if there are values and returns False if not
        # We test the logic through _export_field which is the main entry point
        result = self.document._export_field("nfe40_IBSCBSTot", None, None)
        # Should not return False when there are values
        self.assertIsNotNone(result)

    def test_export_many2one_ibscbstot_without_values(self):
        """Test _export_many2one for IBSCBSTot without values"""
        # Test through _export_field which is the main entry point
        result = self.document._export_field("nfe40_IBSCBSTot", None, None)
        self.assertFalse(result)

    def test_export_field_ibscbs_base_fallback(self):
        """Test _export_field for IBSCBS uses price_gross as base fallback"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # No ibs_base or cbs_base, should use price_gross
        line.write({"ibs_value": 10.0})

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        # Should use price_gross (100.0) as base
        self.assertEqual(result.gIBSCBS.vBC, "100.00")

    def test_export_field_ibscbs_ibs_municipal_zero(self):
        """Test _export_field for IBSCBS sets IBS Municipal to zero"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write({"ibs_value": 10.0})

        result = line._export_field("nfe40_IBSCBS", None, None)
        self.assertIsNotNone(result)
        # IBS Municipal should be zero
        self.assertEqual(result.gIBSCBS.gIBSMun.vIBSMun, "0.00")
        self.assertEqual(result.gIBSCBS.gIBSMun.pIBSMun, "0.0000")


@tagged("post_install", "-at_install")
class TestNFeVItemVNFTot(TransactionCase):
    """Test vItem and vNFTot export in NFe documents (NT 2025.002)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref("base.main_company")
        cls.icms_cst_00 = cls.env.ref("l10n_br_fiscal.cst_icms_00")

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "vat": "65910976000147",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "list_price": 100.0,
            }
        )

        # Document with a real fiscal operation so that the document
        # fiscal totals are computed (see l10n_br_fiscal.document.mixin)
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )

    def _build_det_binding(self, line):
        """Build the real det binding for a document line"""
        return line._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.det"
        )

    def _build_total_binding(self):
        """Build the real total binding for the document"""
        return self.document._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.total"
        )

    def test_export_det_binding_vitem_with_ibs_cbs(self):
        """Test det binding exports vItem when the document has IBS/CBS"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write({"ibs_value": 0.1, "ibs_base": 100.0, "cbs_value": 0.9})

        self.assertGreater(line.fiscal_amount_total, 0.0)
        det = self._build_det_binding(line)
        self.assertEqual(det.vItem, f"{line.fiscal_amount_total:.2f}")

    def test_export_det_binding_vitem_mixed_lines(self):
        """Test all lines export vItem when only one line has IBS/CBS"""
        line_with = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line_without = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 50.0,
            }
        )
        line_with.write({"ibs_value": 0.1, "ibs_base": 100.0, "cbs_value": 0.9})

        self.assertGreater(self.document.fiscal_amount_total, 0.0)
        det_with = self._build_det_binding(line_with)
        det_without = self._build_det_binding(line_without)
        total = self._build_total_binding()

        self.assertIsNotNone(det_with.vItem)
        self.assertIsNotNone(det_without.vItem)
        self.assertEqual(
            Decimal(det_with.vItem) + Decimal(det_without.vItem),
            Decimal(total.vNFTot),
        )
        self.assertEqual(
            Decimal(total.vNFTot),
            Decimal(total.ICMSTot.vNF),
        )
        self.assertEqual(
            Decimal(total.vNFTot),
            Decimal(f"{self.document.fiscal_amount_total:.2f}"),
        )

    def test_export_det_binding_vitem_with_discount(self):
        """Test vItem uses the fiscal total instead of the gross price"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write({"discount_value": 10.0, "ibs_value": 0.1, "ibs_base": 90.0})

        self.assertNotEqual(line.price_gross, line.fiscal_amount_total)
        det = self._build_det_binding(line)
        self.assertEqual(det.vItem, f"{line.fiscal_amount_total:.2f}")

    def test_export_total_binding_with_vnftot(self):
        """Test total binding exports vNFTot along with IBSCBSTot"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        line.write({"ibs_value": 0.1, "ibs_base": 100.0, "cbs_value": 0.9})

        self.assertGreater(self.document.fiscal_amount_total, 0.0)
        total = self._build_total_binding()
        self.assertIsNotNone(total.IBSCBSTot)
        self.assertEqual(total.vNFTot, f"{self.document.fiscal_amount_total:.2f}")

    def test_export_bindings_absent_without_ibs_cbs(self):
        """Test vItem and vNFTot are absent when there is no IBS/CBS"""
        # Regression guard for the legacy behavior: it must stay green
        # before and after the fix (it is not red-green evidence)
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )

        det = self._build_det_binding(line)
        total = self._build_total_binding()
        self.assertIsNone(det.vItem)
        self.assertIsNone(total.vNFTot)
        self.assertIsNone(total.IBSCBSTot)

    def test_export_field_vitem_and_vnftot_direct(self):
        """Test direct _export_field calls for vItem and vNFTot"""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "icms_cst_id": self.icms_cst_00.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        self.assertFalse(line._export_field("nfe40_vItem", None, None))
        self.assertFalse(self.document._export_field("nfe40_vNFTot", None, None))

        line.write({"ibs_value": 0.1, "ibs_base": 100.0})
        self.assertEqual(
            line._export_field("nfe40_vItem", None, None),
            f"{line.fiscal_amount_total:.2f}",
        )
        self.assertEqual(
            self.document._export_field("nfe40_vNFTot", None, None),
            f"{self.document.fiscal_amount_total:.2f}",
        )
