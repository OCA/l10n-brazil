# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import zipfile
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_cnab_structure.models.cnab_data_management import (
    UPGRADE_FILES,
)


@tagged("post_install", "-at_install")
class TestCnabDataManagement(TransactionCase):
    """
    Unit tests for CNAB Data Management model.
    Covers backup, restore, upgrade flows, permissions, and validations.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CnabData = cls.env["cnab.data.management"]
        cls.PixKeyType = cls.env["cnab.pix.key.type"]
        cls.cnab_structure = cls.env.ref(
            "l10n_br_cnab_structure.cnab_itau_240", raise_if_not_found=False
        )
        cls.user_standard = cls.env["res.users"].create(
            {
                "name": "Standard User",
                "login": "std_user_cnab",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )

    def _create_dummy_data(self):
        """Helper to create some data for backup tests."""
        return self.PixKeyType.create(
            {
                "name": "Test Key",
                "description": "Test Key Description",
                "code": "TK",
                "key_type": "email",
                "cnab_structure_id": self.cnab_structure.id,
            }
        )

    def test_backup_no_records_usererror(self):
        """Test backup raising UserError when no records found."""
        self.PixKeyType.search([]).unlink()
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "cnab.pix.key.type",
            }
        )
        with self.assertRaises(UserError):
            op.action_process_operation()

    def test_backup_single_model(self):
        """Test backup of a single model."""
        self._create_dummy_data()
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "cnab.pix.key.type",
            }
        )
        op.action_process_operation()

        self.assertEqual(op.operation_status, "completed")
        self.assertTrue(op.backup_file)

        csv_content = base64.b64decode(op.backup_file).decode("utf-8")
        self.assertIn("TK", csv_content)

    def test_backup_complete(self):
        """Test complete backup generation (ZIP file)."""
        self._create_dummy_data()
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "complete",
            }
        )
        op.action_process_operation()

        self.assertEqual(op.operation_status, "completed")
        self.assertTrue(op.backup_file)
        self.assertTrue(op.backup_filename.endswith(".zip"))

        zip_buffer = io.BytesIO(base64.b64decode(op.backup_file))
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            self.assertIn("cnab.pix.key.type.csv", zf.namelist())

    def test_upgrade_counts_files(self):
        """Upgrade should call convert_file for each file and count them."""
        op = self.CnabData.create({"operation_type": "upgrade"})
        with patch(
            "odoo.addons.l10n_br_cnab_structure.models.cnab_data_management.convert_file"
        ) as mock_convert:
            op.action_process_operation()

        self.assertEqual(op.operation_status, "completed")
        self.assertEqual(op.records_processed, len(UPGRADE_FILES))
        self.assertEqual(mock_convert.call_count, len(UPGRADE_FILES))

    def test_restore_success(self):
        """Test successful restore from CSV."""
        ext_ids = self.cnab_structure.get_external_id()
        structure_ext_id = ext_ids.get(self.cnab_structure.id)

        csv_data = (
            f'"id","name","description","code","key_type",'
            f'"cnab_structure_id/id"\n'
            f'"__test_ext_id","Restored Key","Restored Desc",'
            f'"RK","phone","{structure_ext_id}"'
        )
        b64_data = base64.b64encode(csv_data.encode("utf-8"))

        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_file": b64_data,
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )
        op._compute_detected_model()

        op.action_process_operation()
        self.assertEqual(op.operation_status, "completed")
        self.assertEqual(op.records_processed, 1)

        restored = self.PixKeyType.search([("code", "=", "RK")])
        self.assertTrue(restored)
        self.assertIn("RK", restored.name)
        self.assertEqual(restored.cnab_structure_id.id, self.cnab_structure.id)

    def test_restore_failures_validationerror(self):
        """Test restore raising ValidationError for missing CSV file."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )
        op._compute_detected_model()

        op.csv_file = False
        with self.assertRaisesRegex(ValidationError, "Please upload a CSV"):
            op.action_process_operation()

    def test_restore_failures_usererror(self):
        """Test restore raising UserError for malformed CSV (header only)."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
                "csv_file": base64.b64encode(b'"id","name"\n'),
            }
        )
        op._compute_detected_model()

        with self.assertRaises(UserError):
            op.action_process_operation()

    def test_restore_invalid_encoding(self):
        """Test restore with invalid encoding raises UnicodeDecodeError."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
                "csv_file": base64.b64encode(b"\xff\xfe\x00\x00"),
            }
        )
        op._compute_detected_model()

        with self.assertRaises(UnicodeDecodeError):
            op.action_process_operation()

    def test_restore_load_errors_validationerror(self):
        """When load returns error messages, a ValidationError must be raised."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )
        op._compute_detected_model()
        content = (
            '"id","name","description","code","key_type","cnab_structure_id/id"\n'
            '"__x","N","D","C","email","l10n_br_cnab_structure.any"\n'
        )
        op.csv_file = base64.b64encode(content.encode("utf-8"))

        model_cls = type(self.env["cnab.pix.key.type"])
        with patch.object(
            model_cls,
            "load",
            return_value={
                "messages": [{"type": "error", "message": "bad row"}],
                "ids": [],
            },
        ):
            with self.assertRaises(UserError):
                op.action_process_operation()

    def test_restore_success_with_load_ids(self):
        """Restore success should record count from load ids and complete."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )
        op._compute_detected_model()
        content = (
            '"id","name","description","code","key_type","cnab_structure_id/id"\n'
            '"__x","N","D","C","email","l10n_br_cnab_structure.any"\n'
        )
        op.csv_file = base64.b64encode(content.encode("utf-8"))

        model_cls = type(self.env["cnab.pix.key.type"])
        with patch.object(
            model_cls,
            "load",
            return_value={"messages": [], "ids": [101, 102]},
        ):
            op.action_process_operation()
        self.assertEqual(op.operation_status, "completed")
        self.assertEqual(op.records_processed, 2)

    def test_upgrade_execution(self):
        """Test upgrade operation uses convert_file."""
        op = self.CnabData.create(
            {
                "operation_type": "upgrade",
            }
        )

        with patch("odoo.tools.convert_file"):
            op.action_process_operation()

        self.assertEqual(op.operation_status, "completed")

    def test_restore_many_errors_truncation(self):
        """Test error message truncation when more than 5 errors."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )

        errors = [
            {
                "type": "error",
                "message": f"Error {i}: Something went wrong with record {i}",
            }
            for i in range(10)
        ]
        mock_result = {
            "ids": [],
            "messages": errors,
        }

        csv_data = "id,name\ntest1,Test\n"
        file_content = base64.b64encode(csv_data.encode())
        op.write({"csv_file": file_content})
        op._compute_detected_model()

        with patch("odoo.models.BaseModel.load", return_value=mock_result):
            with self.assertRaises(ValidationError) as cm:
                op.action_process_operation()

            error_message = str(cm.exception)
            self.assertIn("... and 5 more errors", error_message)
            for i in range(5):
                self.assertIn(f"Error {i}:", error_message)
            self.assertNotIn("Error 5:", error_message)

    def test_unlink_locked_operation(self):
        """Test unlink checks immutable lock."""
        self._create_dummy_data()
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "cnab.pix.key.type",
            }
        )
        op.action_process_operation()
        op.action_lock_operation()

        with self.assertRaises(UserError) as cm:
            op.with_user(self.user_standard).unlink()

        self.assertIn("locked", str(cm.exception).lower())

    def test_restore_operation_branch(self):
        """Test explicit restore operation type execution."""
        op = self.CnabData.create(
            {
                "operation_type": "restore",
                "csv_filename": "cnab.pix.key.type.csv",
            }
        )
        op._compute_detected_model()

        mock_result = {"ids": [1, 2, 3], "messages": []}

        csv_data = "id,name\ntest1,Test 1\ntest2,Test 2\ntest3,Test 3\n"
        file_content = base64.b64encode(csv_data.encode())
        op.write({"csv_file": file_content})

        with patch("odoo.models.BaseModel.load", return_value=mock_result):
            op.action_process_operation()

            self.assertEqual(op.operation_status, "completed")
            self.assertEqual(op.operation_type, "restore")

    def test_locking_and_permissions(self):
        """Test locking mechanism and permission checks."""
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "complete",
                "operation_status": "completed",
            }
        )
        self.assertTrue(op.is_locked)

        with self.assertRaisesRegex(UserError, "You cannot modify a locked operation"):
            op.with_user(self.user_standard).write({"name": "Try Change"})

        with self.assertRaisesRegex(UserError, "You cannot modify a locked operation"):
            op.with_user(self.user_standard).unlink()

        op.write({"name": "Admin Change"})
        self.assertEqual(op.name, "Admin Change")

        op_draft = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "complete",
                "operation_status": "draft",
            }
        )
        with self.assertRaisesRegex(ValidationError, "Only completed or error"):
            op_draft.action_lock_operation()

        op_draft.operation_status = "error"
        op_draft.action_lock_operation()
        self.assertEqual(op_draft.operation_status, "locked")

    def test_locked_write_followers_is_allowed(self):
        """Writing only follower/activity fields on locked record is allowed."""
        op = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "complete",
                "operation_status": "completed",
            }
        )
        self.assertTrue(op.is_locked)
        op.write({"message_follower_ids": [(5, 0, 0)]})
        op.write({"activity_ids": [(5, 0, 0)]})

    def test_reset_to_draft(self):
        """Test reset to draft restricted to system admins."""
        self._create_dummy_data()
        op = self.CnabData.create(
            {"operation_type": "backup", "target_model": "cnab.pix.key.type"}
        )
        op.action_process_operation()
        self.assertTrue(op.backup_file)
        self.assertTrue(op.backup_filename)
        op.operation_status = "error"

        with self.assertRaisesRegex(UserError, "Only system administrators"):
            op.with_user(self.user_standard).action_reset_to_draft()

        op.action_reset_to_draft()
        self.assertEqual(op.operation_status, "draft")
        self.assertEqual(op.records_processed, 0)
        self.assertFalse(op.backup_file)
        self.assertFalse(op.backup_filename)

    def test_onchanges_and_computes(self):
        """Test onchange methods and computed fields."""
        op = self.CnabData.create(
            {
                "operation_type": "backup",
            }
        )

        op.operation_type = "restore"
        op._onchange_operation_type()
        self.assertIn("Restore", op.name)

        op.is_complete_backup = True
        op._onchange_is_complete_backup()
        self.assertEqual(op.target_model, "complete")

        op.is_complete_backup = False
        op._onchange_is_complete_backup()
        op.target_model = "cnab.pix.key.type"
        op._onchange_target_model()
        self.assertFalse(op.is_complete_backup)

        op.target_model = "complete"
        op._onchange_target_model()
        self.assertTrue(op.is_complete_backup)

        op.operation_type = "restore"
        op.csv_filename = "cnab.pix.key.type.csv"
        op._compute_detected_model()
        self.assertEqual(op.detected_model.model, "cnab.pix.key.type")

        op.csv_filename = "unknown_file.csv"
        op._compute_detected_model()
        self.assertFalse(op.detected_model)

        op.operation_type = "restore"
        op.csv_filename = "CNAB.PIX.KEY.TYPE.CSV"
        op._compute_detected_model()
        self.assertTrue(op.detected_model)
        self.assertEqual(op.detected_model.model, "cnab.pix.key.type")

        op.operation_status = "draft"
        self.assertFalse(op.is_locked)
        op.operation_status = "completed"
        self.assertTrue(op.is_locked)
        op.operation_status = "error"
        self.assertTrue(op.is_locked)
        op.operation_status = "locked"
        self.assertTrue(op.is_locked)

    def test_validation_start(self):
        """Test validation logic before operation starts."""
        op_restore = self.CnabData.create({"operation_type": "restore"})
        with self.assertRaisesRegex(ValidationError, "Please upload a CSV"):
            op_restore.action_process_operation()

        op_restore.csv_file = base64.b64encode(b"data")
        op_restore.csv_filename = "random.csv"
        with self.assertRaisesRegex(ValidationError, "Could not detect"):
            op_restore.action_process_operation()

        op_backup = self.CnabData.create({"operation_type": "backup"})
        op_backup.target_model = False
        with self.assertRaisesRegex(ValidationError, "Please select a Target Model"):
            op_backup.action_process_operation()

        op_locked = self.CnabData.create(
            {
                "operation_type": "backup",
                "target_model": "complete",
                "operation_status": "completed",
            }
        )
        with self.assertRaisesRegex(ValidationError, "Cannot process a locked"):
            op_locked.action_process_operation()
