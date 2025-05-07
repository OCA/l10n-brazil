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
    - Inheriting models can override `_get_xml_id_name()` to specify the
      naming pattern (the default implementation returns None and disables
      the mixin behavior for the record).
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

        Inheriting models can override this method to specify their
        naming pattern. The default implementation returns None, meaning
        the record is not tracked by the mixin: no ir.model.data entry
        is generated on create and the write() consistency check is
        skipped. This is the desired behavior for purely user managed
        records (e.g. l10n_br_fiscal.document.serie,
        l10n_br_fiscal.document.type) and for data models for which no
        convention has been defined yet.

        :param self: A singleton recordset of the inheriting model.
        :return: The string to be used as the 'name' field in ir.model.data.
                 Return None or False if an XML ID cannot/should not be generated
                 for this specific record based on its current state.
        :rtype: str | None
        """
        return None

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
        _logger.debug(
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
        names_before = {}
        for record in self:
            original_ids[record.id] = tuple(
                map(
                    lambda imd: imd.name,
                    filter(lambda imd: imd.res_id == record.id, existing_data),
                )
            )
            try:
                names_before[record.id] = record._get_xml_id_name()
            except Exception:
                # if the convention cannot be computed from the current
                # values, we cannot enforce it either.
                names_before[record.id] = None

        res = super().write(vals)

        for record in self:
            original = original_ids[record.id]
            if not original:
                continue
            name_before = names_before[record.id]
            # Only enforce the consistency check for records whose xml_id
            # actually followed the naming convention before the write.
            # Legacy data records with exceptional xml_ids (e.g.
            # tax_cofins_seminc, tax_icms_regulation_ac_ac_icms_suspencao,
            # tax_piscofins_4310_001) don't match their computed name and
            # should not be blocked by false positives.
            if name_before is None or name_before != original[0]:
                continue
            name_after = record._get_xml_id_name()
            if name_after is not None and name_after != original[0]:
                raise UserError(
                    _(
                        "Writing these values %(vals)s is forbidden in this record "
                        "because this record is tracked by the xml_id "
                        "%(module)s.%(xml_id_name)s and these values would "
                        "mean an xml_id like %(module)s.%(new_xml_id_name)s "
                        "instead! So if you need a record with these values you "
                        "can archive this record and create a new one instead. "
                        "(The proper xml_id will be created by the %(module)s "
                        "module).",
                        vals=vals,
                        module=record._xml_id_module,
                        xml_id_name=original[0],
                        new_xml_id_name=name_after,
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
            "Toggled noupdate = False for %s records %s",
            self._name,
            imds.mapped("res_id"),
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
            "Toggled noupdate = True for %s records %s",
            self._name,
            imds.mapped("res_id"),
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
        Efficiently finds records without an XML ID via SQL and creates them.

        If called on an empty recordset (e.g. `env['my.model'].fill_missing_xml_ids()`),
        it scans the entire table.
        If called on specific records, it filters only those.
        """

        if self:
            # Filter based on IDs in self
            query = f"""
                SELECT m.id
                FROM "{self._table}" m
                LEFT JOIN ir_model_data d ON (
                    d.res_id = m.id AND
                    d.model = %s
                )
                WHERE d.id IS NULL AND m.id IN %s
            """
            params = (self._name, tuple(self.ids))
        else:
            # Scan whole table (Optimization for hooks)
            query = f"""
                SELECT m.id
                FROM "{self._table}" m
                LEFT JOIN ir_model_data d ON (
                    d.res_id = m.id AND
                    d.model = %s
                )
                WHERE d.id IS NULL
            """
            params = (self._name,)

        self.env.cr.execute(query, params)
        missing_ids = [row[0] for row in self.env.cr.fetchall()]

        if not missing_ids:
            return

        _logger.info(
            "L10n Br Fiscal: Found %s orphan records in %s. Generating XML IDs...",
            len(missing_ids),
            self._name,
        )

        DataModelSudo = self.env["ir.model.data"].sudo()
        for record in self.browse(missing_ids):
            try:
                self._create_missing_xml_id(record, DataModelSudo)
            except Exception as e:
                _logger.error(
                    "Failed to generate XML ID for %s ID %s: %s",
                    self._name,
                    record.id,
                    e,
                )
