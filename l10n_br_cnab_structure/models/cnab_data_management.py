# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import csv
import io
import os
import tempfile
import zipfile
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import convert_file

OPERATION_STATUS = [
    ("draft", "Draft"),
    ("processing", "Processing"),
    ("completed", "Completed"),
    ("error", "Error"),
    ("locked", "Locked"),
]

OPERATION_TYPE = [
    ("backup", "Backup"),
    ("upgrade", "Upgrade"),
    ("restore", "Restore"),
]

UPGRADE_FILES = [
    "data/l10n_br_cnab.structure.csv",
    "data/l10n_br_cnab.batch.csv",
    "data/cnab.payment.way.csv",
    "data/l10n_br_cnab.line.csv",
    "data/cnab.line.field.group.csv",
    "data/l10n_br_cnab.line.field.csv",
    "data/cnab.line.group.field.condition.csv",
    "data/cnab.occurrence.csv",
    "data/cnab.pix.key.type.csv",
    "data/cnab.pix.transfer.type.csv",
]

FILENAME_TO_MODEL = {
    os.path.basename(f_path).lower(): os.path.splitext(os.path.basename(f_path))[0]
    for f_path in UPGRADE_FILES
}

TARGET_MODELS = [
    ("cnab.line.field.group", "CNAB Line Field Group"),
    ("cnab.line.group.field.condition", "CNAB Line Group Field Condition"),
    ("cnab.occurrence", "CNAB Occurrence"),
    ("cnab.payment.way", "CNAB Payment Way"),
    ("cnab.pix.key.type", "CNAB PIX Key Type"),
    ("cnab.pix.transfer.type", "CNAB PIX Transfer Type"),
    ("l10n_br_cnab.batch", "CNAB Batch"),
    ("l10n_br_cnab.line", "CNAB Line"),
    ("l10n_br_cnab.line.field", "CNAB Line Field"),
    ("l10n_br_cnab.structure", "CNAB Structure"),
]

TARGET_MODELS_SELECTION = [("complete", "Complete Backup (All Models)")] + TARGET_MODELS

EXCLUDED_FIELDS = {
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "__last_update",
    "display_name",
}


class CnabDataManagement(models.Model):
    """
    Manage backup, restore, and upgrade operations for CNAB data structures.
    """

    _name = "cnab.data.management"
    _description = "CNAB Data Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Operation Name",
        required=True,
        default=lambda self: _("New CNAB Operation"),
        tracking=True,
    )
    operation_status = fields.Selection(
        selection=OPERATION_STATUS,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        default="backup",
        required=True,
        tracking=True,
    )
    target_model = fields.Selection(
        selection=TARGET_MODELS_SELECTION,
        default="complete",
        tracking=True,
        help="Select the model to backup or choose 'Complete Backup' for all.",
    )
    is_complete_backup = fields.Boolean(
        string="Complete Backup",
        default=True,
        help="If checked, all CNAB models will be backed up.",
    )
    csv_file = fields.Binary(
        attachment=True,
        help="Upload the CSV file for restore operations.",
    )
    csv_filename = fields.Char()
    backup_file = fields.Binary(
        readonly=True,
        attachment=True,
        copy=False,
    )
    backup_filename = fields.Char(copy=False)
    detected_model = fields.Many2one(
        comodel_name="ir.model",
        compute="_compute_detected_model",
        store=True,
        help="Model detected automatically from the uploaded CSV filename.",
    )
    records_processed = fields.Integer(
        readonly=True,
        default=0,
        copy=False,
    )
    is_locked = fields.Boolean(
        compute="_compute_is_locked",
        store=True,
        help="Operation is locked when completed, in error, or manually locked.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    @api.depends("operation_status")
    def _compute_is_locked(self):
        for record in self:
            record.is_locked = record.operation_status in (
                "completed",
                "error",
                "locked",
            )

    @api.depends("csv_filename", "operation_type")
    def _compute_detected_model(self):
        for record in self:
            model_id = False
            if record.operation_type == "restore" and record.csv_filename:
                filename_base = os.path.splitext(record.csv_filename)[0].lower()
                model_name = FILENAME_TO_MODEL.get(
                    record.csv_filename.lower(), filename_base
                )
                model = self.env["ir.model"].search(
                    [("model", "=", model_name)], limit=1
                )
                if model:
                    model_id = model.id
            record.detected_model = model_id

    @api.onchange("operation_type")
    def _onchange_operation_type(self):
        if self.operation_type:
            self.name = _("CNAB %(type)s - %(date)s") % {
                "type": dict(OPERATION_TYPE).get(
                    self.operation_type, self.operation_type
                ),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    @api.onchange("is_complete_backup")
    def _onchange_is_complete_backup(self):
        if self.is_complete_backup:
            self.target_model = "complete"
        elif self.target_model == "complete":
            self.target_model = False

    @api.onchange("target_model")
    def _onchange_target_model(self):
        if self.target_model == "complete":
            self.is_complete_backup = True
        else:
            self.is_complete_backup = False

    def _check_immutable_lock(self):
        """Ensure locked operations cannot be modified by non-system users."""
        for record in self:
            if (
                record.is_locked
                and not self.env.is_superuser()
                and not self.env.user.has_group("base.group_system")
            ):
                raise UserError(
                    _(
                        "You cannot modify a locked operation. "
                        "Please contact a system administrator."
                    )
                )

    def write(self, vals):
        if not set(vals.keys()).issubset({"message_follower_ids", "activity_ids"}):
            self._check_immutable_lock()
        return super().write(vals)

    def unlink(self):
        self._check_immutable_lock()
        return super().unlink()

    def action_process_operation(self):
        """Execute the selected operation (backup, upgrade, restore)."""
        self.ensure_one()
        self._validate_operation_start()
        self.write({"operation_status": "processing"})

        result = {}
        if self.operation_type == "backup":
            result = self._execute_backup()
        elif self.operation_type == "upgrade":
            result = self._execute_upgrade()
        elif self.operation_type == "restore":
            result = self._execute_restore()

        vals = {
            "operation_status": "completed",
            "records_processed": result.get("count", 0),
        }
        if result.get("backup_data"):
            vals.update(
                {
                    "backup_file": result["backup_data"],
                    "backup_filename": result["backup_filename"],
                }
            )
        self.write(vals)
        self.message_post(
            body=result.get("message", _("Operation completed successfully.")),
            message_type="notification",
        )
        return True

    def _validate_operation_start(self):
        """Validate the operation before execution starts."""
        if self.is_locked:
            raise ValidationError(
                _("Cannot process a locked operation. Create a new one.")
            )
        if self.operation_type == "restore":
            if not self.csv_file:
                raise ValidationError(_("Please upload a CSV file to restore."))
            if not self.detected_model:
                raise ValidationError(
                    _(
                        "Could not detect the target model from the filename. "
                        "Please ensure the filename matches a valid CNAB model."
                    )
                )
        if self.operation_type == "backup":
            if not self.target_model:
                raise ValidationError(
                    _("Please select a Target Model or choose 'Complete Backup'.")
                )

    def action_lock_operation(self):
        """Manually lock the operation to prevent further changes."""
        for record in self:
            if record.operation_status not in ("completed", "error"):
                raise ValidationError(
                    _("Only completed or error operations can be locked.")
                )
            record.write({"operation_status": "locked"})
        return True

    def action_reset_to_draft(self):
        """Reset the operation to draft status (system administrators only)."""
        if not self.env.user.has_group("base.group_system"):
            raise UserError(
                _("Only system administrators can reset operations to draft.")
            )
        self.write(
            {
                "operation_status": "draft",
                "records_processed": 0,
                "backup_file": False,
                "backup_filename": False,
            }
        )
        return True

    def _execute_backup(self):
        if self.target_model == "complete":
            return self._create_complete_backup()
        return self._create_model_backup(self.target_model)

    def _execute_upgrade(self):
        """Reload original module CSV files to upgrade CNAB structures."""
        count = 0
        for csv_file_path in UPGRADE_FILES:
            convert_file(
                self.env.cr,
                "l10n_br_cnab_structure",
                csv_file_path,
                {},
                mode="upgrade",
                noupdate=False,
                kind="data",
            )
            count += 1
        return {
            "count": count,
            "message": _("Upgrade executed successfully. %d files reloaded.") % count,
        }

    def _execute_restore(self):
        """Restore data from the uploaded CSV file."""
        return self._restore_model_from_upload(self.detected_model.model)

    def _create_complete_backup(self):
        """Generate a ZIP file containing CSVs for all CNAB models."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cnab_complete_backup_{timestamp}.zip"

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, filename)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for model_name, _label in TARGET_MODELS:
                    csv_data = self._export_model_csv(model_name)
                    if csv_data:
                        zip_file.writestr(f"{model_name}.csv", csv_data)

            with open(zip_path, "rb") as f:
                backup_data_raw = f.read()
                backup_data_b64 = base64.b64encode(backup_data_raw)

        self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": backup_data_b64,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/zip",
            }
        )

        return {
            "count": len(TARGET_MODELS),
            "message": _("Complete backup generated successfully."),
            "backup_data": backup_data_b64,
            "backup_filename": filename,
        }

    def _create_model_backup(self, model_name):
        """Generate a CSV backup file for a single model."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_name}_{timestamp}.csv"
        csv_data = self._export_model_csv(model_name)

        if not csv_data:
            raise UserError(_("No records found to backup for model %s.") % model_name)

        backup_data_b64 = base64.b64encode(csv_data.encode("utf-8"))

        self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": backup_data_b64,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "text/csv",
            }
        )

        return {
            "count": max(0, csv_data.count("\n") - 1),
            "message": _("Backup for %s generated successfully.") % model_name,
            "backup_data": backup_data_b64,
            "backup_filename": filename,
        }

    def _export_model_csv(self, model_name):
        """
        Export model data to CSV format using native Odoo export.
        Force 'id' (External ID) as the first column and use '/id'
        suffix for relational fields to get XML IDs.
        """
        Model = self.env[model_name]
        records = Model.search([])

        if not records:
            return ""

        fields_to_export = ["id"]

        for name, field in Model._fields.items():
            if name in EXCLUDED_FIELDS or name == "id":
                continue
            if not field.store:
                continue

            if field.type == "many2one":
                fields_to_export.append(f"{name}/id")
            elif field.type in ("one2many", "many2many"):
                continue
            else:
                fields_to_export.append(name)

        data = records.export_data(fields_to_export).get("datas", [])
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(fields_to_export)
        writer.writerows(data)

        return output.getvalue()

    def _restore_model_from_upload(self, model_name):
        """Restore data using Odoo's native 'load' method."""
        csv_content = base64.b64decode(self.csv_file).decode("utf-8")
        f = io.StringIO(csv_content)
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

        if not header or not data:
            raise UserError(_("CSV file appears to be empty or malformed."))

        result = self.env[model_name].load(header, data)
        if result.get("messages"):
            errors = [
                msg["message"] for msg in result["messages"] if msg["type"] == "error"
            ]
            if errors:
                error_text = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_text += _("\n... and %d more errors.") % (len(errors) - 5)
                raise ValidationError(
                    _("Errors occurred during import:\n%s") % error_text
                )

        imported_count = len(result.get("ids", []))
        return {
            "count": imported_count,
            "message": _("Successfully restored %(count)d records to %(model)s.")
            % {"count": imported_count, "model": model_name},
        }
