# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import operator
import re
from datetime import datetime

from unidecode import unidecode

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, time


class CNABField(models.Model):
    _name = "l10n_br_cnab.line.field"
    _description = "Fields in CNAB lines."
    _order = "cnab_line_id, start_pos"

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})

    computed_name = fields.Char(string="Field", compute="_compute_name")

    ref_name = fields.Char(
        string="Reference Name",
        help="Unique reference name to identify the cnab field, can be used to search"
        " the field content in python expressions in 'Dynamic Content'. "
        "It is generated automatically by aggregating the field name, starting "
        "position and ending position. ex:. 'field_name_001-015'",
        compute="_compute_ref_name",
    )

    meaning = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    cnab_line_id = fields.Many2one(
        "l10n_br_cnab.line",
        readonly=True,
        ondelete="cascade",
        required=True,
        states={"draft": [("readonly", False)]},
    )
    cnab_group_id = fields.Many2one(
        "cnab.line.field.group",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    start_pos = fields.Integer(
        string="Start Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    end_pos = fields.Integer(
        string="End Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    assumed_comma = fields.Integer(
        help="indicates the position of the comma within a numeric field.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type = fields.Selection(
        [
            ("alpha", _("Alphanumeric")),
            ("num", _("Numeric")),
        ],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    related_field_id = fields.Many2one(
        "ir.model.fields", readonly=True, states={"draft": [("readonly", False)]}
    )
    default_value = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    notes = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    size = fields.Integer(compute="_compute_size")

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )
    content_source_model_id = fields.Many2one(
        comodel_name="ir.model", related="cnab_line_id.content_source_model_id"
    )
    content_source_field = fields.Char(
        help="Inform the field with the origin of the content, expressed with"
        " dot notation.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    preview_field = fields.Char(compute="_compute_preview_field")

    resource_ref = fields.Reference(
        string="Reference",
        related="cnab_line_id.resource_ref",
    )

    sending_dynamic_content = fields.Char(
        help="Expression in Python to define the final value of the content,"
        "you can use the following predefined words:\n\n"
        "'content' returns the value of the mapped content source field.\n"
        "'time' class to handle date.\n"
        "'seq_batch' returns the batch sequence.\n"
        "'seq_record_detail' returns the sequence for detail record in the batch.\n"
        "'payment_way_code' return the batch payment way\n"
        "'payment_type_code' return the batch payment type\n"
        "'qty_batches' returns the number of batches\n"
        "'qty_records' returns the number of records\n"
        "'batch_detail_lines' returns a list of batch detail records."
        "'segment_code' returns the code of the segment defined in the header"
        " of the line.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    content_dest_model_id = fields.Many2one(
        comodel_name="ir.model", related="cnab_line_id.content_dest_model_id"
    )
    content_dest_field = fields.Char(
        string="Content Destination Field",
        help="Inform the field with the origin of the content, expressed with"
        " dot notation.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    return_dynamic_content = fields.Char(
        readonly=True, states={"draft": [("readonly", False)]}
    )

    def action_change_field(self):
        """
        Action for open select field wizard"
        """
        mapping_type = self.cnab_line_id.current_view
        return self._open_select_field_wizard(mapping_type)

    def action_change_field_sending(self):
        """
        Action for open select field wizard
        for mapping sending content
        """
        return self._open_select_field_wizard("sending")

    def action_change_field_return(self):
        """
        Action for open select field wizard
        for mapping return content
        """
        return self._open_select_field_wizard("return")

    def _open_select_field_wizard(self, mapping_type):
        if mapping_type == "sending":
            notation_field = self.content_source_field
            model_id = self.content_source_model_id
        if mapping_type == "return":
            notation_field = self.content_dest_field
            model_id = self.content_dest_model_id
        return {
            "name": _("Change Dot Notation Field"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "field.select.wizard",
            "target": "new",
            "context": {
                "default_cnab_field_id": self.id,
                "default_notation_field": notation_field,
                "default_model_id": model_id.id,
                "default_current_view": mapping_type,
            },
        }

    def _compute_ref_name(self):
        for rec in self:
            name = rec.name or ""
            name = unidecode(name.replace(" ", "_").lower())
            rec.ref_name = f"{rec.start_pos}_{rec.end_pos}_{name}"

    @api.depends("resource_ref", "content_source_field", "sending_dynamic_content")
    def _compute_preview_field(self):
        for rec in self:
            preview = ""
            if rec.resource_ref:
                try:
                    ref_name, preview = rec.output(rec.resource_ref)
                    preview = preview.replace(" ", "⎵")
                except (ValueError, SyntaxError) as exc:
                    preview = str(exc)
            rec.preview_field = preview

    def output(self, resource_ref, **kwargs):
        "Compute output value for this field"
        for rec in self:
            value = rec.default_value or ""
            if rec.content_source_field and resource_ref:
                value = (
                    operator.attrgetter(rec.content_source_field)(resource_ref) or ""
                )
            if rec.sending_dynamic_content:
                value = rec.eval_compute_value(
                    value, rec.sending_dynamic_content, **kwargs
                )
            value = self.format(rec.size, rec.type, value)
            return self.ref_name, value

    def format(self, size, value_type, value):
        """formats the value according to the specification"""
        if isinstance(value, float):
            value = f"{value:.{self.assumed_comma}f}"
        value = str(value)
        if value_type == "num":
            value = re.sub(r"\W+", "", value)
            value = value.zfill(size)
        if value_type == "alpha":
            value = unidecode(value).upper()
            value = value.ljust(size)
        value = value[:size]
        return value

    def eval_compute_value(self, content, python_expression, **kwargs):
        "Execute python code and return computed value"
        self.ensure_one()
        safe_eval_dict = {
            "content": content,
            "time": time,
            "datetime": datetime,
            "seq_batch": kwargs.get("seq_batch", ""),
            "seq_record_detail": kwargs.get("seq_record_detail", ""),
            "payment_way_code": kwargs.get("payment_way_code", ""),
            "payment_type_code": kwargs.get("payment_type_code", ""),
            "qty_batches": kwargs.get("qty_batches", ""),
            "qty_records": kwargs.get("qty_records", ""),
            "batch_detail_lines": kwargs.get("batch_detail_lines", []),
            "segment_code": self.cnab_line_id.segment_code or "",
        }
        return safe_eval(python_expression, safe_eval_dict)

    def _compute_name(self):
        for fld in self:
            fld.computed_name = (
                f"{fld.name} - Meaning: {fld.meaning} - Pos: "
                f"{fld.start_pos}:{fld.end_pos} - Type: {fld.type}"
            )

    @api.depends("start_pos", "end_pos")
    def _compute_size(self):
        for f in self:
            f.size = f.end_pos - f.start_pos + 1

    def unlink(self):
        lines = self.filtered(lambda line: line.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Field which is not draft !"))
        return super().unlink()

    def action_review(self):
        self.write({"state": "review"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_draft(self):
        self.write({"state": "draft"})

    def check_field(self):
        if self.start_pos > self.end_pos:
            raise UserError(
                _(
                    f"{self.name} in {self.cnab_line_id}: Start position is greater"
                    " than end position."
                )
            )
