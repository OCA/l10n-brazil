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

        # Tax classification (cClassTrib) required to export the IBSCBS group
        cls.tax_classification = cls.env.ref("l10n_br_fiscal.tax_classification_000001")

        # Create fiscal document
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )

    def _create_line(self, **extra_vals):
        vals = {
            "document_id": self.document.id,
            "product_id": self.product.id,
            "quantity": 1.0,
            "price_unit": 100.0,
        }
        vals.update(extra_vals)
        return self.env["l10n_br_fiscal.document.line"].create(vals)

    def _export_ibscbs(self, line):
        """Build the IBSCBS binding through the framework per tag hooks"""
        return line.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_IBSCBS", self.env["nfe.40.imposto"])

    def _export_ibscbstot(self):
        """Build the IBSCBSTot binding through the framework per tag hooks"""
        return self.document.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_IBSCBSTot", self.env["nfe.40.total"])

    def test_export_ibscbs_with_ibs_value(self):
        """Test IBSCBS export with IBS value"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        # Write computed fields directly for testing
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        # CST is only exported when the line has an IBS CST
        self.assertIsNone(result.CST)
        self.assertEqual(result.cClassTrib, "000001")
        self.assertIsNotNone(result.gIBSCBS)
        self.assertEqual(result.gIBSCBS.vBC, "100.00")
        self.assertEqual(result.gIBSCBS.gIBSUF.pIBSUF, "10.0000")
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "10.00")
        self.assertEqual(result.gIBSCBS.vIBS, "10.00")

    def test_export_ibscbs_with_cbs_value(self):
        """Test IBSCBS export with CBS value"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write(
            {
                "cbs_value": 5.0,
                "cbs_percent": 5.0,
                "cbs_base": 100.0,
            }
        )

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.gIBSCBS.gCBS.pCBS, "5.0000")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_ibscbs_with_both_values(self):
        """Test IBSCBS export with both IBS and CBS values"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
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

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.gIBSCBS.vIBS, "10.00")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_ibscbs_gred_parent_qualified(self):
        """Test gRed uses the parent qualified hooks (gIBSUF vs gCBS)"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_percent": 10.0,
                "ibs_base": 100.0,
                "ibs_reduction": 60.0,
                "cbs_value": 5.0,
                "cbs_percent": 5.0,
                "cbs_base": 100.0,
                "cbs_reduction": 30.0,
            }
        )

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        # each parent gets its own reduction
        self.assertEqual(result.gIBSCBS.gIBSUF.gRed.pRedAliq, "60.0000")
        self.assertEqual(result.gIBSCBS.gCBS.gRed.pRedAliq, "30.0000")
        # gIBSMun has no gRed hook
        self.assertIsNone(result.gIBSCBS.gIBSMun.gRed)

    def test_export_ibscbs_gred_absent_without_reduction(self):
        """Test gRed is omitted when there is no reduction"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"ibs_value": 10.0, "ibs_base": 100.0, "cbs_value": 5.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertIsNone(result.gIBSCBS.gIBSUF.gRed)
        self.assertIsNone(result.gIBSCBS.gCBS.gRed)

    def test_export_ibscbs_without_tax_classification(self):
        """Test IBSCBS is not exported without a tax classification"""
        line = self._create_line()
        line.write({"ibs_value": 10.0, "ibs_base": 100.0})

        result = self._export_ibscbs(line)
        self.assertFalse(result)

    def test_export_ibscbs_without_values(self):
        """Test IBSCBS export with a tax classification but no values"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.cClassTrib, "000001")
        self.assertEqual(result.gIBSCBS.vBC, "0.00")
        self.assertEqual(result.gIBSCBS.vIBS, "0.00")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "0.00")

    def test_export_ibscbs_with_tax_classification(self):
        """Test IBSCBS export uses the tax classification code"""
        tax_classification = self.env.ref("l10n_br_fiscal.tax_classification_410002")

        line = self._create_line(tax_classification_id=tax_classification.id)
        line.write({"ibs_value": 10.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.cClassTrib, "410002")

    def test_export_ibscbs_with_ibs_cst(self):
        """Test IBSCBS export with IBS CST"""
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

        line = self._create_line(
            tax_classification_id=self.tax_classification.id,
            ibs_cst_id=ibs_cst.id,
        )
        line.write({"ibs_value": 10.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.CST, "50")

    def test_export_ibscbs_with_cbs_cst(self):
        """Test IBSCBS export with CBS CST"""
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

        line = self._create_line(
            tax_classification_id=self.tax_classification.id,
            cbs_cst_id=cbs_cst.id,
        )
        line.write({"cbs_value": 5.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        # The CST comes only from the IBS CST, there is no CBS fallback
        self.assertIsNone(result.CST)

    def test_export_ibscbs_hook_only_populates_dict(self):
        """Test the IBSCBS hook only populates export_dict with values"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)

        export_dict = {}
        line._export_tag_nfe_40_ibscbs([], None, export_dict)
        # CST is only set when the line has an IBS CST
        self.assertNotIn("CST", export_dict)
        self.assertEqual(export_dict.get("cClassTrib"), "000001")

    def test_export_ibscbs_hook_without_tax_classification(self):
        """Test the IBSCBS hook leaves export_dict empty without classification"""
        line = self._create_line()

        export_dict = {}
        line._export_tag_nfe_40_ibscbs([], None, export_dict)
        self.assertFalse(export_dict)

    def test_export_ibscbs_base_from_ibs_base(self):
        """Test IBSCBS export takes the base from ibs_base"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"ibs_value": 10.0, "ibs_base": 100.0, "cbs_base": 100.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.gIBSCBS.vBC, "100.00")
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "10.00")

    def test_export_ibscbs_base_falls_back_to_cbs_base(self):
        """Test vBC falls back to cbs_base on a CBS only line"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        # no IBS tax on this line, only CBS
        line.write({"cbs_value": 5.0, "cbs_percent": 5.0, "cbs_base": 100.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        # vBC is the base shared by IBS and CBS, it must match gCBS
        self.assertEqual(result.gIBSCBS.vBC, "100.00")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_ibscbs_ibs_municipal_zero(self):
        """Test IBSCBS export sets IBS Municipal to zero"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"ibs_value": 10.0})

        result = self._export_ibscbs(line)
        self.assertIsNotNone(result)
        # IBS Municipal should be zero
        self.assertEqual(result.gIBSCBS.gIBSMun.vIBSMun, "0.00")
        self.assertEqual(result.gIBSCBS.gIBSMun.pIBSMun, "0.0000")

    def test_compute_nfe40_ibscbstot_fields_empty(self):
        """Test _compute_nfe40_IBSCBSTot_fields with no lines"""
        self.document.fiscal_line_ids = False
        self.document._compute_nfe40_IBSCBSTot_fields()

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 0.0)
        self.assertEqual(self.document.nfe40_vIBS, 0.0)
        self.assertEqual(self.document.nfe40_vCBS, 0.0)

    def test_compute_nfe40_ibscbstot_fields_with_ibs(self):
        """Test _compute_nfe40_IBSCBSTot_fields with IBS values"""
        line = self._create_line()
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
        line = self._create_line()
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
        line1 = self._create_line()
        line1.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        line2 = self._create_line(price_unit=200.0)
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

    def test_export_ibscbstot_with_values(self):
        """Test IBSCBSTot export with IBS/CBS values"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write(
            {
                "ibs_value": 10.0,
                "ibs_base": 100.0,
            }
        )

        result = self._export_ibscbstot()
        self.assertIsNotNone(result)
        self.assertEqual(result.vBCIBSCBS, "100.00")
        self.assertIsNotNone(result.gIBS)
        self.assertEqual(result.gIBS.vIBS, "10.00")
        self.assertEqual(result.gIBS.gIBSUF.vIBSUF, "10.00")
        self.assertIsNotNone(result.gCBS)

    def test_export_ibscbstot_without_tax_classification(self):
        """Test IBSCBSTot is not exported when no line has a classification"""
        line = self._create_line()
        line.write({"ibs_value": 10.0, "ibs_base": 100.0})

        result = self._export_ibscbstot()
        self.assertFalse(result)


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

        # Tax classification (cClassTrib) required to export the IBSCBS group
        cls.tax_classification = cls.env.ref("l10n_br_fiscal.tax_classification_000001")

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

    def _create_line(self, **extra_vals):
        vals = {
            "document_id": self.document.id,
            "product_id": self.product.id,
            "icms_cst_id": self.icms_cst_00.id,
            "quantity": 1.0,
            "price_unit": 100.0,
        }
        vals.update(extra_vals)
        return self.env["l10n_br_fiscal.document.line"].create(vals)

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
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"ibs_value": 0.1, "ibs_base": 100.0, "cbs_value": 0.9})

        self.assertGreater(line.fiscal_amount_total, 0.0)
        det = self._build_det_binding(line)
        self.assertEqual(det.vItem, f"{line.fiscal_amount_total:.2f}")

    def test_export_det_binding_ibscbs_group(self):
        """Test the det binding exports IBSCBS via the per tag hooks"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
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

        det = self._build_det_binding(line)
        self.assertIsNotNone(det.imposto.IBSCBS)
        self.assertEqual(det.imposto.IBSCBS.cClassTrib, "000001")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.vBC, "100.00")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.vIBS, "10.00")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.gIBSUF.vIBSUF, "10.00")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.gCBS.vCBS, "5.00")

    def test_export_det_binding_no_ibscbs_group(self):
        """Test the det binding does not export IBSCBS without classification"""
        line = self._create_line()

        det = self._build_det_binding(line)
        self.assertIsNone(det.imposto.IBSCBS)

    def test_export_det_binding_vitem_mixed_lines(self):
        """Test all lines export vItem when only one line has IBS/CBS"""
        line_with = self._create_line(tax_classification_id=self.tax_classification.id)
        line_without = self._create_line(price_unit=50.0)
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
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"discount_value": 10.0, "ibs_value": 0.1, "ibs_base": 90.0})

        self.assertNotEqual(line.price_gross, line.fiscal_amount_total)
        det = self._build_det_binding(line)
        self.assertEqual(det.vItem, f"{line.fiscal_amount_total:.2f}")

    def test_export_total_binding_with_vnftot(self):
        """Test total binding exports vNFTot along with IBSCBSTot"""
        line = self._create_line(tax_classification_id=self.tax_classification.id)
        line.write({"ibs_value": 0.1, "ibs_base": 100.0, "cbs_value": 0.9})

        self.assertGreater(self.document.fiscal_amount_total, 0.0)
        total = self._build_total_binding()
        self.assertIsNotNone(total.IBSCBSTot)
        self.assertEqual(total.vNFTot, f"{self.document.fiscal_amount_total:.2f}")

    def test_export_bindings_absent_without_ibs_cbs(self):
        """Test vItem and vNFTot are absent when there is no IBS/CBS"""
        # Regression guard for the legacy behavior: it must stay green
        # before and after the fix (it is not red-green evidence)
        line = self._create_line()

        det = self._build_det_binding(line)
        total = self._build_total_binding()
        self.assertIsNone(det.vItem)
        self.assertIsNone(total.vNFTot)
        self.assertIsNone(total.IBSCBSTot)

    def test_export_field_vitem_and_vnftot_direct(self):
        """Test direct _export_field calls for vItem and vNFTot"""
        line = self._create_line()
        self.assertFalse(line._export_field("nfe40_vItem", None, None))
        self.assertFalse(self.document._export_field("nfe40_vNFTot", None, None))

        line.write(
            {
                "tax_classification_id": self.tax_classification.id,
                "ibs_value": 0.1,
                "ibs_base": 100.0,
            }
        )
        self.assertEqual(
            line._export_field("nfe40_vItem", None, None),
            f"{line.fiscal_amount_total:.2f}",
        )
        self.assertEqual(
            self.document._export_field("nfe40_vNFTot", None, None),
            f"{self.document.fiscal_amount_total:.2f}",
        )


@tagged("post_install", "-at_install")
class TestNFeIBSCBSFiscalOperation(TransactionCase):
    """Test IBSCBS export with the tax classification coming from the
    fiscal operation line instead of being written on the line"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref("base.main_company")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_transferencia")
        cls.fiscal_operation_line = cls.env.ref(
            "l10n_br_fiscal.fol_manifesto_mercadoria"
        )
        cls.tax_classification = cls.env.ref("l10n_br_fiscal.tax_classification_410002")

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "cnpj_cpf": "65910976000147",
            }
        )

        # fiscal_type 00 (goods for resale) so the fiscal operation line
        # matched is fol_manifesto_mercadoria, the one carrying the
        # 410002 tax classification
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "list_price": 100.0,
                "fiscal_type": "00",
            }
        )

        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": cls.fiscal_operation.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": cls.product.id,
                "fiscal_operation_id": cls.fiscal_operation.id,
                "icms_cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_00").id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )

    def _build_det_binding(self):
        return self.line._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.det"
        )

    def test_tax_classification_from_fiscal_operation_line(self):
        """Test the line takes the tax classification from the operation line"""
        self.assertEqual(self.line.fiscal_operation_line_id, self.fiscal_operation_line)
        self.assertEqual(self.line.tax_classification_id, self.tax_classification)
        self.assertEqual(self.line.tax_classification_id.code, "410002")
        # 410002 maps the IBS/CBS immunity taxes (CST 410, zero rate)
        self.assertEqual(self.line.ibs_cst_id.code, "410")
        self.assertEqual(self.line.cbs_cst_id.code, "410")

    def test_export_det_binding_ibscbs_group(self):
        """Test the det binding exports IBSCBS from the operation line data"""
        det = self._build_det_binding()

        self.assertIsNotNone(det.imposto.IBSCBS)
        self.assertEqual(det.imposto.IBSCBS.CST, "410")
        self.assertEqual(det.imposto.IBSCBS.cClassTrib, "410002")
        # immunity: the group is exported with zero values
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.vBC, "0.00")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.vIBS, "0.00")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.gIBSUF.pIBSUF, "0.0000")
        self.assertEqual(det.imposto.IBSCBS.gIBSCBS.gCBS.vCBS, "0.00")
        # no reduction configured, so no gRed
        self.assertIsNone(det.imposto.IBSCBS.gIBSCBS.gIBSUF.gRed)
        self.assertIsNone(det.imposto.IBSCBS.gIBSCBS.gCBS.gRed)
        # CST 410 keeps the gIBSCBS choice branch
        self.assertIsNone(det.imposto.IBSCBS.gIBSCBSMono)

    def test_export_total_binding_ibscbstot(self):
        """Test the totals are exported for a document with a classification"""
        total = self.document._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.total"
        )

        self.assertIsNotNone(total.IBSCBSTot)
        self.assertEqual(total.IBSCBSTot.vBCIBSCBS, "0.00")
        self.assertEqual(total.IBSCBSTot.gIBS.vIBS, "0.00")
        self.assertEqual(total.IBSCBSTot.gCBS.vCBS, "0.00")
        self.assertEqual(total.vNFTot, f"{self.document.fiscal_amount_total:.2f}")

    def test_export_det_binding_vitem(self):
        """Test vItem is exported for every line of such a document"""
        det = self._build_det_binding()
        self.assertEqual(det.vItem, f"{self.line.fiscal_amount_total:.2f}")
