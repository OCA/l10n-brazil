# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import operator
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, time


class CNABField(models.Model):

    _name = "l10n_br_cnab.line.field"
    _description = "Fields in CNAB lines."

    name = fields.Char(readonly=True, states={"draft": [("readonly", "=", False)]})
    meaning = fields.Char(readonly=True, states={"draft": [("readonly", "=", False)]})
    cnab_line_id = fields.Many2one(
        "l10n_br_cnab.line",
        readonly=True,
        ondelete="cascade",
        required=True,
        states={"draft": [("readonly", "=", False)]},
    )
    start_pos = fields.Integer(
        string="Start Position",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    end_pos = fields.Integer(
        string="End Position",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    type = fields.Selection(
        [
            ("alpha", _("Alphanumeric")),
            ("num", _("Numeric")),
        ],
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    related_field_id = fields.Many2one(
        "ir.model.fields", readonly=True, states={"draft": [("readonly", "=", False)]}
    )
    default_value = fields.Char(
        readonly=True, states={"draft": [("readonly", "=", False)]}
    )
    notes = fields.Char(readonly=True, states={"draft": [("readonly", "=", False)]})
    size = fields.Integer(compute="_compute_size")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )
    related_ir_model_id = fields.Many2one(
        "ir.model", string="Related Model", related="cnab_line_id.related_ir_model_id"
    )
    dot_notation_field = fields.Char(
        string="Related Field",
    )

    preview_field = fields.Char(compute="_compute_preview_field")

    resource_ref = fields.Reference(
        string="Reference",
        related="cnab_line_id.resource_ref",
    )

    python_code = fields.Text()

    def action_change_field(self):
        "action for change for field"
        return {
            "name": _("Change Dot Notation Field"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "field.select.wizard",
            "target": "new",
            "context": {
                "default_cnab_field_id": self.id,
                "default_dot_notation_field": self.dot_notation_field,
            },
        }

    @api.depends("resource_ref", "dot_notation_field", "python_code", "default_value")
    def _compute_preview_field(self):
        for rec in self:
            rec.preview_field = ""
            if rec.resource_ref:
                try:
                    rec.preview_field = rec.compute_output_value(rec.resource_ref)
                except (ValueError, SyntaxError) as exc:
                    rec.preview_field = str(exc)

    def compute_output_value(self, resource_ref):
        "Compute output value for this field"
        # TODO aqui vamos aplicar todas a regras para montar o valor final.
        for rec in self:
            value = ""
            if rec.dot_notation_field and resource_ref:
                value = operator.attrgetter(rec.dot_notation_field)(resource_ref)
                value = str(value)
                # Tratamento para campos númericos.
                if rec.type == "num":
                    value = re.sub(r"\W+", "", value)

            # aplica os valores dafault.
            if not value and rec.default_value:
                value = rec.default_value

            # aplica zeros ou brancos para valores não preenchidos.
            if not value:
                if rec.type == "num":
                    value = value.zfill(rec.size)
                if rec.type == "alpha":
                    value = value.ljust(rec.size)

            if rec.python_code:
                value = rec.eval_compute_value(value)
            return value

    def eval_compute_value(self, value):
        "Execute python code and return computed value"
        self.ensure_one()
        safe_eval_dict = {"value": value, "time": time}
        return safe_eval(self.python_code, safe_eval_dict)

    @api.depends("start_pos", "end_pos")
    def _compute_size(self):
        for f in self:
            f.size = f.end_pos - f.start_pos + 1

    def unlink(self):
        lines = self.filtered(lambda l: l.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Field which is not draft !"))
        return super(CNABField, self).unlink()

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
                    f"{self.name} in {self.cnab_line_id}: Start position is greater than end position."
                )
            )
