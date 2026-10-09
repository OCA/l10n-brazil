# Copyright 2024 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests.common import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class SpedEfdPisCofinsPullTest(AccountMoveBRCommon):
    """Test _map_from_odoo implementations for EFD PIS/COFINS registers.

    Uses AccountMoveBRCommon to set up a Brazilian company with fiscal
    configuration, creates NF-e invoices, then verifies that
    button_populate_sped_from_odoo() correctly creates SPED registers
    via the _map_from_odoo methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # PIS tax definition for the company
        cls.pis_tax_definition = cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_pis").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_0_65").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_pis_01").id,
                "state": "approved",
            }
        )

        # COFINS tax definition for the company
        cls.cofins_tax_definition = cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_cofins").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_3").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_cofins_01").id,
                "state": "approved",
            }
        )

        # ICMS tax definition
        cls.icms_tax_definition = cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icms_12").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_00").id,
                "state": "approved",
            }
        )

        # Document series for NF-e (type 55)
        cls.document_55_serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "active": True,
            }
        )

        # Create a sale invoice (NF-e, document type 55)
        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.document_55_serie,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        # Create a purchase invoice
        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.move_in_compra = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="42",
        )

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 Lucro Presumido"
        else:
            company_name = "empresa 2 Lucro Presumido"
        chart_template = cls.env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="3",
            is_industry=True,
            industry_type="00",
            profit_calculation="presumed",
            ripi=True,
            piscofins_id=cls.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            icms_regulation_id=cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            **kwargs,
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        chart_template.load_fiscal_taxes()
        return res

    def test_pull_from_odoo_registers_created(self):
        """Test that Pull from Odoo creates the expected SPED registers."""
        # Flush any pre-existing registers
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        # Create EFD PIS/COFINS declaration with debug=True
        # (debug mode finds all fiscal documents regardless of state_edoc)
        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )

        # Pull registers from Odoo data
        declaration.button_populate_sped_from_odoo()

        # --- Bloco 0: Reference tables ---

        # 0110 - Tax regime (no _odoo_model, uses declaration.company_id)
        reg_0110 = self.env["l10n_br_sped.efd_pis_cofins.0110"].search([])
        self.assertTrue(reg_0110, "Registro 0110 should be created")
        # Company is Lucro Presumido → COD_INC_TRIB = "2" (Cumulativo)
        self.assertEqual(
            reg_0110.COD_INC_TRIB,
            "2",
            "Lucro Presumido company should have COD_INC_TRIB=2",
        )

        # 0140 - Establishment (from res.company)
        reg_0140 = self.env["l10n_br_sped.efd_pis_cofins.0140"].search([])
        self.assertTrue(reg_0140, "Registro 0140 should be created")
        self.assertEqual(reg_0140.NOME, declaration.company_id.legal_name)

        # --- Bloco C: NF-e documents ---

        # C010 - Establishment identification (no _odoo_model)
        reg_c010 = self.env["l10n_br_sped.efd_pis_cofins.c010"].search([])
        self.assertTrue(reg_c010, "Registro C010 should be created")

        # --- Bloco A/D/F: Other blocks ---

        # A010 - Service establishment
        reg_a010 = self.env["l10n_br_sped.efd_pis_cofins.a010"].search([])
        self.assertTrue(reg_a010, "Registro A010 should be created")

        # D010 - Transport establishment
        reg_d010 = self.env["l10n_br_sped.efd_pis_cofins.d010"].search([])
        self.assertTrue(reg_d010, "Registro D010 should be created")

        # F010 - Other operations establishment
        reg_f010 = self.env["l10n_br_sped.efd_pis_cofins.f010"].search([])
        self.assertTrue(reg_f010, "Registro F010 should be created")

    def test_pull_from_odoo_generates_valid_sped(self):
        """Test that SPED text can be generated after pulling from Odoo."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        # Generate SPED text — should not raise
        sped_text = declaration._generate_sped_text()
        self.assertTrue(sped_text, "SPED text should not be empty")

        # Verify key register markers are present in the output
        self.assertIn("|0000|", sped_text, "Should contain register 0000")
        self.assertIn("|0110|", sped_text, "Should contain register 0110")
        self.assertIn("|0140|", sped_text, "Should contain register 0140")
        self.assertIn("|C010|", sped_text, "Should contain register C010")

    def test_pull_from_odoo_0150_participants(self):
        """Test that 0150 register is created for document partners."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        # If there are fiscal documents with partners, 0150 should have entries
        if declaration.fiscal_document_partner_ids:
            reg_0150 = self.env["l10n_br_sped.efd_pis_cofins.0150"].search([])
            self.assertTrue(
                reg_0150,
                "Registro 0150 should be created when documents have partners",
            )
            # Verify partner data is mapped
            for reg in reg_0150:
                self.assertTrue(reg.NOME, "Partner NOME should not be empty")
                self.assertTrue(reg.COD_PART, "Partner COD_PART should not be empty")

    def test_pull_from_odoo_c100_nfe(self):
        """Test that C100 registers are created for NF-e documents."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        # Check if C100 registers were created for NF-e documents
        reg_c100 = self.env["l10n_br_sped.efd_pis_cofins.c100"].search([])
        nfe_docs = declaration.fiscal_document_ids.filtered(
            lambda d: d.document_type_id.code in ("01", "1B", "04", "55", "65")
        )
        if nfe_docs:
            self.assertTrue(
                reg_c100,
                "C100 registers should be created for NF-e documents",
            )
            self.assertEqual(
                len(reg_c100),
                len(nfe_docs),
                "One C100 register per NF-e document",
            )

            # Check C170 line items exist for each C100
            reg_c170 = self.env["l10n_br_sped.efd_pis_cofins.c170"].search([])
            if nfe_docs.mapped("fiscal_line_ids"):
                self.assertTrue(
                    reg_c170,
                    "C170 registers should be created for NF-e line items",
                )

    def test_pull_from_odoo_0200_products(self):
        """Test that 0200 register is created for products."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        if declaration.fiscal_product_ids:
            reg_0200 = self.env["l10n_br_sped.efd_pis_cofins.0200"].search([])
            self.assertTrue(
                reg_0200,
                "Registro 0200 should be created when documents have products",
            )
            for reg in reg_0200:
                self.assertTrue(
                    reg.DESCR_ITEM, "Product DESCR_ITEM should not be empty"
                )

    def test_pull_from_odoo_0190_uom(self):
        """Test that 0190 register is created for units of measure."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        if declaration.fiscal_uom_ids:
            reg_0190 = self.env["l10n_br_sped.efd_pis_cofins.0190"].search([])
            self.assertTrue(
                reg_0190,
                "Registro 0190 should be created when documents have UoMs",
            )

    def test_pull_from_odoo_0400_operations(self):
        """Test that 0400 register is created for fiscal operations."""
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")

        declaration = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {
                "debug": True,
            }
        )
        declaration.button_populate_sped_from_odoo()

        if declaration.fiscal_operation_ids:
            reg_0400 = self.env["l10n_br_sped.efd_pis_cofins.0400"].search([])
            self.assertTrue(
                reg_0400,
                "Registro 0400 should be created for fiscal operations",
            )
            for reg in reg_0400:
                self.assertTrue(
                    reg.DESCR_NAT, "Operation DESCR_NAT should not be empty"
                )
