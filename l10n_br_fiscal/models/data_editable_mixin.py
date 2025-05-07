# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class EditableDataMixin(models.AbstractModel):
    """
    Mixin to automatically manage ir.model.data entries for records.

    Features:
    - Automatically creates ir.model.data entries for manually created records.
    - Skips creation if an entry already exists (e.g., from XML/CSV import).
    - Requires inheriting models to define `_xml_id_module` and implement
      `_get_xml_id_name()` to specify the naming pattern.
    - Provides `get_records_without_xmlid()` to find records lacking an XML ID.
    - Provides `fill_missing_xml_ids()` to backfill missing XML IDs for
      existing records.
    - Prevent writing values inconsistent with record xml_id.
    - Allow to toggle update/noupdate mode.
    """

    _name = "l10n_br_fiscal.data.editable.mixin"
    _description = "Mixin for Automatic ir.model.data Management"

    # To be defined in the inheriting model
    _xml_id_module = "l10n_br_fiscal"

    active = fields.Boolean(default=True)

    def _get_xml_id_name(self):
        """
        Calculate the specific 'name' for the ir.model.data entry.
        This method MUST be implemented by the inheriting model.

        :param self: A singleton recordset of the inheriting model.
        :return: The string to be used as the 'name' field in ir.model.data.
                 Return None or False if an XML ID cannot/should not be generated
                 for this specific record based on its current state.
        :rtype: str | None
        """
        if self._name in [
            "l10n_br_fiscal.document.serie",
            "l10n_br_fiscal.document.type",
        ]:
            return (
                None
            )  # disable the mixin effect because it's cleary a user managed record
        raise NotImplementedError(
            _("Method `_get_xml_id_name` must be implemented in model %s.") % self._name
        )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("install_mode") or self.env.context.get("module"):
            self = self.with_context(tracking_disable=True)  # faster creation
            return super().create(vals_list)

        records = super().create(vals_list)
        if not records:
            return records

        # Check which records already have an XML ID
        new_ids = records.ids
        DataModel = self.env["ir.model.data"]
        _logger.info(
            "Mixin Create: Searching ir.model.data for model '%s' and res_ids %s",
            self._name,
            new_ids,
        )
        existing_data = DataModel.search(
            [("model", "=", self._name), ("res_id", "in", new_ids)]
        )
        ids_with_xmlid = set(existing_data.mapped("res_id"))

        # Filter records needing an XML ID
        records_to_process = records.filtered(lambda r: r.id not in ids_with_xmlid)

        # Process records needing an XML ID
        if records_to_process:
            DataModelSudo = DataModel.sudo()
            for record in records_to_process:
                try:
                    # Call the helper method for the specific record
                    self._create_missing_xml_id(record, DataModelSudo)
                except Exception as e:
                    # Log error but continue with other records
                    _logger.error(
                        "Mixin Create: Error calling _create_missing_xml_id for "
                        "%s (%s): %s",
                        record._name,
                        record.id,
                        e,
                        exc_info=True,
                    )

        return records

    def write(self, vals):
        """Prevent writing values inconsistent with the record xml_id."""

        if self.env.context.get("install_mode") or self.env.context.get("module"):
            # self = self.with_context(tracking_disable=True)  # faster write; risky?
            return super().write(vals)

        existing_data = (
            self.env["ir.model.data"]
            .sudo()
            .search([("model", "=", self._name), ("res_id", "in", self.ids)])
        )
        original_ids = {}
        for record in self:
            original_ids[record.id] = tuple(
                map(
                    lambda imd: imd.name,
                    filter(lambda imd: imd.res_id == record.id, existing_data),
                )
            )

        res = super().write(vals)

        for record in self:
            if (
                original_ids[record.id]
                and record._get_xml_id_name() is not None
                and record._get_xml_id_name() != original_ids[record.id][0]
            ):
                raise UserError(
                    _(
                        "Writing these values %(vals)s is forbidden in this record "
                        "because this record is tracked by the xml_id "
                        "l10n_br_fiscal.%(xml_id_name)s and these values would "
                        "mean an xml_id like l10n_br_fiscal.%(new_xml_id_name)s "
                        "instead! So if you need a record with these values you "
                        "can archive this record and create a new one instead. "
                        "(The proper xml_id will be created by the l10n_br_fiscal "
                        "module).",
                        vals=vals,
                        xml_id_name=original_ids[record.id][0],
                        new_xml_id_name=record._get_xml_id_name(),
                    )
                )
        return res

    def action_archive(self):
        if not self.env.user.has_group("l10n_br_fiscal.group_manager"):
            raise AccessError(_("You don't have permission to archive records."))
        return super().action_archive()

    def action_unarchive(self):
        if not self.env.user.has_group("l10n_br_fiscal.group_manager"):
            raise AccessError(_("You don't have permission to unarchive records."))
        return super().action_unarchive()

    def button_set_update(self):
        if (
            not self.env.user.has_group("l10n_br_fiscal.group_manager")
            and not self.env.user._is_superuser()
            and not self.env.user._is_system()
        ):
            raise AccessError(_("You don't have permission to set records for update!"))

        imds = (
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("model", "=", self._name),
                    ("res_id", "in", self.ids),
                    ("noupdate", "=", True),
                ]
            )
        )
        _logger.warning(
            f"Toogle noupdate = True for {self._name} records {imds.mapped('res_id')}"
        )
        return imds.sudo().write({"noupdate": False})

    def button_set_noupdate(self):
        if (
            not self.env.user.has_group("l10n_br_fiscal.group_manager")
            and not self.env.user._is_superuser()
            and not self.env.user._is_system()
        ):
            raise AccessError(_("You don't have permission to disable records update!"))

        imds = (
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("model", "=", self._name),
                    ("res_id", "in", self.ids),
                    ("noupdate", "=", False),
                ]
            )
        )
        _logger.warning(
            f"Toogle noupdate = False for {self._name} records {imds.mapped('res_id')}"
        )
        return imds.sudo().write({"noupdate": True})

    def _create_missing_xml_id(self, record, DataModel):
        """Internal helper to create the ir.model.data record."""
        record.ensure_one()

        xml_id_name = record._get_xml_id_name()
        if xml_id_name:
            # Check if the specific name already exists
            if DataModel.search_count(
                [("module", "=", self._xml_id_module), ("name", "=", xml_id_name)]
            ):
                return

            DataModel.create(
                {
                    "module": self._xml_id_module,
                    "name": xml_id_name,
                    "model": record._name,
                    "res_id": record.id,
                    "noupdate": True,
                }
            )

    # --- Utility Methods ---

    def get_records_without_xmlid(self):
        """
        Returns a recordset containing only the records from self
        that do not have a corresponding ir.model.data entry.

        :param self: The input recordset.
        :return: A recordset of the same model.
        :rtype: odoo.models.Model
        """
        if not self:
            return self.browse()

        record_ids = self.ids
        if not record_ids:
            return self.browse()

        data_model = self.env["ir.model.data"]
        existing_data = data_model.search(
            [("model", "=", self._name), ("res_id", "in", record_ids)]
        )
        ids_with_xmlid = set(existing_data.mapped("res_id"))

        ids_without_xmlid = [rid for rid in record_ids if rid not in ids_with_xmlid]

        # Return as recordset for easier chaining/operations
        return self.browse(ids_without_xmlid)

    def fill_missing_xml_ids(self):
        """
        Finds records in the current recordset (`self`) without an XML ID
        and attempts to create one based on the model's pattern.

        Use this for backfilling records created before this mixin was active.
        Example Usage: self.env['your.model'].search([]).fill_missing_xml_ids()
        """
        records_to_process = self.get_records_without_xmlid()
        DataModelSudo = self.env["ir.model.data"].sudo()

        for record in records_to_process:
            if not DataModelSudo.search_count(
                [("model", "=", record._name), ("res_id", "=", record.id)]
            ):
                self._create_missing_xml_id(record, DataModelSudo)
