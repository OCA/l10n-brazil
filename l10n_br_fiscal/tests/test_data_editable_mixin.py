# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class TestIrModelDataEditableMixinOnNcm(TransactionCase):
    """
    Tests for the l10n_br_fiscal.data.editable.mixin integrated
    with the l10n_br_fiscal.ncm model.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
            )
        )
        cls.Ncm = cls.env["l10n_br_fiscal.ncm"]
        cls.ncm_model_name = "l10n_br_fiscal.ncm"
        cls.ncm_module_name = "l10n_br_fiscal"
        cls.IrModelData = cls.env["ir.model.data"].sudo()

    def _create_ncm(self, code_suffix, name_suffix=None, **kwargs):
        code = f"9999.99.{code_suffix:02d}"
        name = f"Test NCM {name_suffix or code_suffix}"
        vals = {"code": code, "name": name, **kwargs}
        return self.Ncm.create(vals)

    def _get_xml_id(self, record):
        return self.IrModelData.search(
            [
                ("module", "=", self.ncm_module_name),
                ("model", "=", self.ncm_model_name),
                ("res_id", "=", record.id),
            ]
        )

    # --- Test Methods Adjusted Below ---

    def test_01_create_generates_xmlid(self):
        """Test that creating an NCM record generates an ir.model.data entry."""
        # This test should now pass after fixing the mixin's create method
        record_code_suffix = 1
        record = self._create_ncm(record_code_suffix)
        expected_xml_id_name = f"ncm_{record.code.replace('.', '')}"

        self.assertTrue(record, "NCM Record should be created")
        xml_id_record = self._get_xml_id(record)
        self.assertEqual(
            len(xml_id_record), 1, "Exactly one XML ID should be created for NCM"
        )
        self.assertEqual(
            xml_id_record.name,
            expected_xml_id_name,
            "NCM XML ID name should match the pattern",
        )
        self.assertTrue(xml_id_record.noupdate, "XML ID noupdate flag should be True")

    def test_02_create_skips_existing_xmlid(self):
        """
        Test that create does not create a duplicate if XML ID
        already exists for NCM.
        """
        record_code_suffix = 2
        manual_xml_id_name = f"manual_ncm_{record_code_suffix}"

        # Create NCM first
        record = self._create_ncm(record_code_suffix)
        # Manually remove the auto-generated one (if any) to simulate import
        self._get_xml_id(record).unlink()

        # Manually create an ir.model.data
        manual_xml_id = self.IrModelData.create(
            {
                "module": self.ncm_module_name,
                "name": manual_xml_id_name,
                "model": self.ncm_model_name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
        self.assertTrue(manual_xml_id, "Manual XML ID should be created")

        # Verify no duplicate was made and manual one remains
        xml_id_records = self._get_xml_id(record)
        self.assertEqual(
            len(xml_id_records), 1, "Still exactly one XML ID should exist for NCM"
        )
        self.assertEqual(
            xml_id_records.name,
            manual_xml_id_name,
            "XML ID name should be the manually created one",
        )
        self.assertTrue(
            xml_id_records.noupdate,
            "XML ID noupdate flag should be the manually set one (True)",
        )

    def test_03_create_skips_in_test_mode(self):
        """Test that create *does not* skip just for test_enable=True."""
        # This test's premise changes: test_enable should NOT prevent creation.
        # The skipping happens for install_mode=True or module=True in context.
        # We can rename or repurpose this test to ensure normal creation works.
        # Or simply trust test_01 covers normal creation. Let's keep it simple:
        # Test that default test creation *does* create an ID.
        record = self._create_ncm(3)
        self.assertTrue(record)
        xml_id_record = self._get_xml_id(record)
        # ASSERTION IS NOW assertTrue
        self.assertTrue(xml_id_record, "XML ID *should* be created in normal test mode")

    def test_04_create_skips_in_install_mode(self):
        """
        Test that create *does* skip XML ID gen when
        context indicates install mode.
        """
        # This test remains valid as it checks the context key
        record = self.Ncm.with_context(install_mode=True).create(
            {"code": "9999.99.04", "name": "Test NCM 04 Install"}
        )
        self.assertTrue(record)
        xml_id_record = self._get_xml_id(record)
        self.assertFalse(
            xml_id_record, "No XML ID should be created for NCM in install mode"
        )

    def test_05_get_records_without_xmlid(self):
        """Test the get_records_without_xmlid method on NCM."""
        # Record 1: Gets XML ID automatically
        rec1 = self._create_ncm(61)
        # Record 2: Create WITH code, but manually remove its XML ID
        rec2 = self._create_ncm(62)
        rec2_xml_id = self._get_xml_id(rec2)
        self.assertTrue(rec2_xml_id, "Rec2 should initially get an XML ID")
        rec2_xml_id.unlink()  # Remove it for the test

        # Record 3: Manually add XML ID (after removing auto-one)
        rec3 = self._create_ncm(63)
        self._get_xml_id(rec3).unlink()  # Remove auto-one first
        self.IrModelData.create(
            {
                "module": self.ncm_module_name,
                "name": "manual_ncm_63",
                "model": self.ncm_model_name,
                "res_id": rec3.id,
            }
        )

        all_records = rec1 | rec2 | rec3

        # Verify state before calling the method
        self.assertTrue(self._get_xml_id(rec1), "Rec1 should have XML ID")
        self.assertFalse(
            self._get_xml_id(rec2), "Rec2 should NOT have XML ID (manually removed)"
        )
        self.assertTrue(self._get_xml_id(rec3), "Rec3 should have manual XML ID")

        # Call the method
        records_without_id = all_records.get_records_without_xmlid()

        # Assertions
        self.assertEqual(
            len(records_without_id), 1, "Should find exactly one record without XML ID"
        )
        self.assertEqual(
            records_without_id.id, rec2.id, "The record found should be rec2"
        )

    def test_06_fill_missing_xml_ids(self):
        """Test the fill_missing_xml_ids utility method on NCM."""
        # Record 1: Create WITH code, manually remove XML ID. This one should be filled.
        rec1 = self._create_ncm(71)
        rec1_xml_id = self._get_xml_id(rec1)
        self.assertTrue(rec1_xml_id, "Rec1 should initially get an XML ID")
        rec1_xml_id.unlink()  # Remove it
        expected_xml_id_name_rec1 = f"ncm_{rec1.code.replace('.', '')}"

        # Record 2: Create WITH code, keep its XML ID. This one should NOT be touched.
        rec2 = self._create_ncm(72)
        self.assertTrue(self._get_xml_id(rec2), "Rec2 should have XML ID and keep it")

        # Record 3: Will test skipping if pattern returns None (if possible)
        # For NCM, this is hard to test as code is required. Let's omit for now.

        records_to_check = rec1 | rec2

        # Call the fill method
        records_to_check.fill_missing_xml_ids()

        # Check XML IDs after filling
        xml_id_rec1_after = self._get_xml_id(rec1)
        self.assertTrue(xml_id_rec1_after, "Rec1 should now have an XML ID after fill")
        self.assertEqual(
            xml_id_rec1_after.name,
            expected_xml_id_name_rec1,
            "Rec1 XML ID name should be correct",
        )
        self.assertTrue(xml_id_rec1_after.noupdate, "Rec1 noupdate should be True")

        self.assertTrue(
            self._get_xml_id(rec2), "Rec2 should still have its original XML ID"
        )

    def test_07_write_does_not_create_xmlid(self):
        """Test that write() itself does not trigger XML ID creation on NCM."""
        # Setup: Create record WITH code, remove its XML ID
        record = self._create_ncm(81)
        initial_xml_id = self._get_xml_id(record)
        self.assertTrue(initial_xml_id, "Record should have XML ID initially")
        initial_xml_id.unlink()
        self.assertFalse(
            self._get_xml_id(record),
            "Record should not have XML ID after manual removal",
        )

        # Write some other field (e.g., name)
        record.write({"name": "Updated NCM Name 81"})

        # Verify that write did NOT create the ID
        self.assertFalse(
            self._get_xml_id(record), "Record should still not have XML ID after write"
        )

        # Verify fill *does* work now
        record.fill_missing_xml_ids()
        self.assertTrue(
            self._get_xml_id(record), "Record should have XML ID after fill"
        )

    def test_08_write_does_allow_conflicting_values(self):
        """
        Test that write() will not allow writing values
        inconsistent with the xml_id
        """
        record = self._create_ncm(81)
        initial_xml_id = self._get_xml_id(record)
        self.assertTrue(initial_xml_id, "Record should have XML ID initially")
        with self.assertRaises(UserError):
            record.write({"code": "badcode"})

    @mute_logger("odoo.addons.l10n_br_fiscal.models.data_editable_mixin")
    def test_09_update_noupdate(self):
        """Test update / nopupdate toggle"""
        record = self._create_ncm(81)

        user = self.env["res.users"].create(
            {
                "name": "Fiscal User",
                "login": "test_editable_data_user",
                "password": "admin",
                "groups_id": [
                    (4, self.env.ref("l10n_br_fiscal.group_user").id),
                ],
            }
        )
        with self.assertRaises(AccessError):
            record.with_user(user).button_set_update()
        with self.assertRaises(AccessError):
            record.with_user(user).button_set_noupdate()

        manager = self.env["res.users"].create(
            {
                "name": "Fiscal Manager",
                "login": "test_editable_data_manager",
                "password": "admin",
                "groups_id": [
                    (4, self.env.ref("l10n_br_fiscal.group_manager").id),
                ],
            }
        )
        record.with_user(manager).button_set_update()
        self.assertFalse(self._get_xml_id(record).noupdate)
        record.with_user(manager).button_set_noupdate()
        self.assertTrue(self._get_xml_id(record).noupdate)

    def test_10_archive_unarchive(self):
        """Test update / nopupdate toggle"""
        record = self._create_ncm(81)

        user = self.env["res.users"].create(
            {
                "name": "Fiscal User",
                "login": "test_editable_data_user",
                "password": "admin",
                "groups_id": [
                    (4, self.env.ref("l10n_br_fiscal.group_user").id),
                ],
            }
        )
        with self.assertRaises(AccessError):
            record.with_user(user).action_archive()

        manager = self.env["res.users"].create(
            {
                "name": "Fiscal Manager",
                "login": "test_editable_data_manager",
                "password": "admin",
                "groups_id": [
                    (4, self.env.ref("l10n_br_fiscal.group_manager").id),
                ],
            }
        )
        record.with_user(manager).action_archive()
        self.assertFalse(record.active)
        record.with_user(manager).action_unarchive()
        self.assertTrue(record.active)

    def test_11_various_xml_id_names(self):
        """Test the xml ids of some classes were the mixin is injected"""
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_icms_16")._get_xml_id_name(), "tax_icms_16"
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_icms_12_red_26_57")._get_xml_id_name(),
            "tax_icms_12_red_26_57",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_pis_value_26_36")._get_xml_id_name(),
            "tax_pis_value_26_36",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_pis_monofasico_1_67")._get_xml_id_name(),
            "tax_pis_monofasico_1_67",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_pis_value_0_0211")._get_xml_id_name(),
            "tax_pis_value_0_0211",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_ipi_33_86")._get_xml_id_name(),
            "tax_ipi_33_86",
        )

        self.assertEqual(
            self.env.ref("l10n_br_fiscal.service_type_404")._get_xml_id_name(),
            "service_type_404",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.cst_icmssn_300")._get_xml_id_name(),
            "cst_icmssn_300",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.cnae_0116402")._get_xml_id_name(),
            "cnae_0116402",
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.cfop_1120")._get_xml_id_name(), "cfop_1120"
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.nbs_114021100")._get_xml_id_name(),
            "nbs_114021100",
        )

        # PIS/COFINS Tests
        # 1. Monofásico
        pc_mono = self.env["l10n_br_fiscal.tax.pis.cofins"].create(
            {
                "code": "101",
                "name": "Gasolina Monofásico",  # Keyword 'Monofásico'
                "piscofins_type": "product",
            }
        )
        self.assertEqual(pc_mono._get_xml_id_name(), "tax_piscofins_monofasico_101")

        # 2. Simples Nacional
        pc_simples = self.env["l10n_br_fiscal.tax.pis.cofins"].create(
            {
                "code": "000",
                "name": "Regime Simples Nacional",
                "piscofins_type": "company",
            }
        )
        self.assertEqual(
            pc_simples._get_xml_id_name(), "tax_pis_cofins_simples_nacional"
        )

        # 3. Generic Fallback
        pc_generic = self.env["l10n_br_fiscal.tax.pis.cofins"].create(
            {"code": "999", "name": "Operação Genérica", "piscofins_type": "product"}
        )
        self.assertEqual(pc_generic._get_xml_id_name(), "tax_pis_cofins_999")

    def test_12_write_allowed_when_xmlid_does_not_follow_convention(self):
        """
        Records whose existing xml_id does NOT match the naming convention
        (legacy data exceptions) should not be blocked by the write guard.
        Example: tax_cofins_seminc computes as tax_cofins_0.
        """
        tax_seminc = self.env.ref("l10n_br_fiscal.tax_cofins_seminc")
        self.assertNotEqual(tax_seminc._get_xml_id_name(), "tax_cofins_seminc")
        # should not raise UserError:
        tax_seminc.write({"name": "COFINS Sem Incidência"})
        self.assertEqual(tax_seminc.name, "COFINS Sem Incidência")

    def test_13_untracked_model_does_not_crash(self):
        """
        Models inheriting the mixin through l10n_br_fiscal.data.abstract
        but not implementing _get_xml_id_name (e.g. legal.nature) should
        be creatable/writable without crash and stay untracked.
        """
        legal_nature = self.env["l10n_br_fiscal.legal.nature"].create(
            {"code": "9999", "name": "Test Legal Nature"}
        )
        self.assertTrue(legal_nature)
        self.assertIsNone(legal_nature._get_xml_id_name())
        xml_id_record = self.IrModelData.search(
            [
                ("model", "=", "l10n_br_fiscal.legal.nature"),
                ("res_id", "=", legal_nature.id),
            ]
        )
        self.assertFalse(xml_id_record, "No XML ID should be created")
        # write should not crash either:
        legal_nature.write({"name": "Test Legal Nature 2"})

    def test_14_cest_nbm_xml_id_names(self):
        """Test the xml id naming convention for CEST and NBM records."""
        cest = self.env["l10n_br_fiscal.cest"].create(
            {
                "code": "01.002.00",
                "item": "2.0",
                "segment": "01",
                "name": "Test CEST",
            }
        )
        cest_xml_id = self.IrModelData.search(
            [
                ("module", "=", "l10n_br_fiscal"),
                ("model", "=", "l10n_br_fiscal.cest"),
                ("res_id", "=", cest.id),
            ]
        )
        self.assertEqual(cest_xml_id.name, "cest_0100200")

        nbm = self.env["l10n_br_fiscal.nbm"].create(
            {"code": "0000.10.0001", "name": "Test NBM"}
        )
        nbm_xml_id = self.IrModelData.search(
            [
                ("module", "=", "l10n_br_fiscal"),
                ("model", "=", "l10n_br_fiscal.nbm"),
                ("res_id", "=", nbm.id),
            ]
        )
        self.assertEqual(nbm_xml_id.name, "nbm_0000100001")
