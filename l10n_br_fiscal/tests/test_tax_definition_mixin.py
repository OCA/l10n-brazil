# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests.common import TransactionCase


class TestTaxDefinitionMixin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TaxDefinition = cls.env["l10n_br_fiscal.tax.definition"]
        cls.Tax = cls.env["l10n_br_fiscal.tax"]
        cls.State = cls.env["res.country.state"]
        cls.TaxGroup = cls.env["l10n_br_fiscal.tax.group"]

        # Get necessary records
        cls.state_ac = cls.env.ref("base.state_br_ac")
        cls.state_al = cls.env.ref("base.state_br_al")
        cls.tax_group_icms = cls.env.ref("l10n_br_fiscal.tax_group_icms")
        cls.tax_group_icmsfcp = cls.env.ref("l10n_br_fiscal.tax_group_icmsfcp")
        cls.tax_group_icmsst = cls.env.ref("l10n_br_fiscal.tax_group_icmsst")

        # Mock Taxes (simulating existing ones)
        cls.tax_icms_12 = cls.env.ref("l10n_br_fiscal.tax_icms_12")
        cls.tax_icms_nt = cls.env.ref("l10n_br_fiscal.tax_icms_nt")
        cls.tax_icms_suspensao = cls.env.ref("l10n_br_fiscal.tax_icms_suspensao")
        cls.tax_icmsfcp_2 = cls.env.ref("l10n_br_fiscal.tax_icmsfcp_2")
        cls.tax_icmsst_47 = cls.env.ref("l10n_br_fiscal.tax_icmsst_47")

    def test_01_xml_id_icms_internal_numeric_approved(self):
        """Test XML ID generation for Internal ICMS (Approved, Numeric Rate)"""
        # Mimic: tax_icms_regulation_ac_ac_19_default
        # We use tax_icms_12 for test to vary slightly or 19 if available

        # Create a transient definition
        # Using tax_icms_12, state AC->AC, Approved

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icms.id,
                "state_from_id": self.state_ac.id,
                "state_to_ids": [(6, 0, [self.state_ac.id])],
                "tax_id": self.tax_icms_12.id,
                "state": "approved",
                "custom_tax": True,
                "is_taxed": True,
            }
        )

        expected_xml_id = "tax_icms_regulation_ac_ac_12_default"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)

    def test_02_xml_id_icms_internal_nt(self):
        """Test XML ID generation for Internal ICMS (NT - Non Taxed)"""
        # Mimic: tax_icms_regulation_ac_ac_nt

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icms.id,
                "state_from_id": self.state_ac.id,
                "state_to_ids": [(6, 0, [self.state_ac.id])],
                "tax_id": self.tax_icms_nt.id,
                "state": "draft",
                "custom_tax": True,
                "is_taxed": False,
            }
        )

        expected_xml_id = "tax_icms_regulation_ac_ac_nt"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)

    def test_03_xml_id_icms_internal_suspensao(self):
        """Test XML ID generation for Internal ICMS (Suspensao - Special case)"""
        # Mimic: tax_icms_regulation_ac_ac_icms_suspencao
        # Note: tax xml id is tax_icms_suspensao

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icms.id,
                "state_from_id": self.state_ac.id,
                "state_to_ids": [(6, 0, [self.state_ac.id])],
                "tax_id": self.tax_icms_suspensao.id,
                "state": "draft",
                "custom_tax": True,
                "is_taxed": False,
            }
        )

        # Logic enforces 'icms_suspensao' suffix based on tax id
        expected_xml_id = "tax_icms_regulation_ac_ac_icms_suspensao"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)

    def test_04_xml_id_icms_interstate(self):
        """Test XML ID generation for Interstate ICMS"""
        # Mimic: tax_icms_regulation_ac_icms_12

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icms.id,
                "state_from_id": self.state_ac.id,
                "state_to_ids": [(6, 0, [self.state_al.id])],  # Different state
                "tax_id": self.tax_icms_12.id,
                "state": "approved",
                "custom_tax": True,
                "is_taxed": True,
            }
        )

        expected_xml_id = "tax_icms_regulation_ac_icms_12"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)

    def test_05_xml_id_icmsfcp(self):
        """Test XML ID generation for FCP"""
        # Mimic: tax_icmsfcp_2_regulation_al_al

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icmsfcp.id,
                "state_from_id": self.state_al.id,
                "state_to_ids": [(6, 0, [self.state_al.id])],
                "tax_id": self.tax_icmsfcp_2.id,
                "state": "approved",
                "custom_tax": True,
                "is_taxed": True,
            }
        )

        expected_xml_id = "tax_icmsfcp_2_regulation_al_al"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)

    def test_06_xml_id_icmsst(self):
        """Test XML ID generation for ICMS ST"""
        # Mimic: tax_icmsst_definition_sp_mva_47
        # Note: state_from SP.
        sp_state = self.env.ref("base.state_br_sp")

        tax_def = self.TaxDefinition.create(
            {
                "tax_group_id": self.tax_group_icmsst.id,
                "state_from_id": sp_state.id,
                "state_to_ids": [(6, 0, [self.state_al.id])],
                "tax_id": self.tax_icmsst_47.id,
                "state": "approved",
                "custom_tax": True,
                "is_taxed": True,
            }
        )

        expected_xml_id = "tax_icmsst_definition_sp_mva_47"
        generated_xml_id = tax_def._get_xml_id_name()
        self.assertEqual(generated_xml_id, expected_xml_id)
