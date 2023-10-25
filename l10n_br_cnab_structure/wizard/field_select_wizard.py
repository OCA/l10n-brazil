# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FieldSelectWizard(models.TransientModel):
    _name = "field.select.wizard"
    _description = "Field Select Wizard"

    notation_field = fields.Char()

    current_view = fields.Char()

    notation_field_view = fields.Char(
        compute="_compute_notation_field_view",
    )

    cnab_field_id = fields.Many2one(
        comodel_name="l10n_br_cnab.line.field",
        string="CNAB Field",
    )

    model_id = fields.Many2one(
        "ir.model",
        string="Related Model",
    )

    new_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', parent_model_id)]",
    )

    parent_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Parent Model",
        compute="_compute_parent_model_id",
    )

    @api.depends("model_id", "notation_field")
    def _compute_parent_model_id(self):
        model = self.model_id
        if self.notation_field:
            dn_fields = self.notation_field.split(".")
            for fld in dn_fields:
                field_id = self.env["ir.model.fields"].search(
                    [("model_id", "=", model.id), ("name", "=", fld)]
                )
                model = self.env["ir.model"].search([("model", "=", field_id.relation)])
        self.parent_model_id = model

    def _update_dot_notation(self):
        if self.new_field_id:
            if self.current_view == "return" and self.notation_field:
                raise UserError(
                    _(
                        "For the return it is not allowed to map "
                        "sub-fields in more than one level."
                    )
                )
            self.notation_field = self.notation_field or ""
            self.notation_field += "." if self.notation_field else ""
            self.notation_field += self.new_field_id.name

    def action_confirm(self):
        "Action Confirm"
        if self.current_view == "sending":
            self.cnab_field_id.content_source_field = self.notation_field
        if self.current_view == "return":
            self.cnab_field_id.content_dest_field = self.notation_field
        return

    def action_remove_last_field(self):
        "Action Confirm"
        strings = self.notation_field.split(".")[:-1]
        self.notation_field = ".".join(strings)
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "field.select.wizard",
            "target": "new",
            "context": {
                "default_cnab_field_id": self.cnab_field_id.id,
                "default_notation_field": self.notation_field,
                "default_model_id": self.model_id.id,
                "default_current_view": self.current_view,
            },
        }

    @api.depends("notation_field")
    def _compute_notation_field_view(self):
        self.notation_field_view = self.notation_field.replace(".", "→")

    def action_add_field(self):
        "Action Add Field"
        self._update_dot_notation()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "field.select.wizard",
            "target": "new",
            "context": {
                "default_cnab_field_id": self.cnab_field_id.id,
                "default_notation_field": self.notation_field,
                "default_model_id": self.model_id.id,
                "default_current_view": self.current_view,
            },
        }
