# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..cnab.cnab import CnabLine


class CNABLine(models.Model):
    _name = "l10n_br_cnab.line"
    _description = "Lines that make up the CNAB."
    _order = "sequence, id"

    name = fields.Char(compute="_compute_name", store=True)

    sequence = fields.Integer(readonly=True, states={"draft": [("readonly", False)]})

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        ondelete="cascade",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    segment_code = fields.Char(
        states={"draft": [("readonly", False)]},
    )

    content_source_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Content Source",
        help="Related model that will provide the origin of the contents of CNAB"
        "files.",
        compute="_compute_content_source_model_id",
        states={"draft": [("readonly", False)]},
    )

    content_dest_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Content Destination",
        help="Related model that will provide the destination"
        " of the contents of return CNAB files.",
        compute="_compute_dest_source_model_id",
        states={"draft": [("readonly", False)]},
    )

    requerid = fields.Boolean(
        states={"draft": [("readonly", False)]},
    )

    communication_flow = fields.Selection(
        [("sending", "Sending"), ("return", "Return"), ("both", "Sending and Return")],
        required=True,
        states={"draft": [("readonly", False)]},
    )

    current_view = fields.Selection(
        [("general", "General"), ("sending", "Sending"), ("return", "Return")],
        required=True,
        default="general",
        states={"draft": [("readonly", False)]},
    )

    type = fields.Selection(
        [("header", "Header"), ("segment", "Segment"), ("trailer", "Trailer")],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    field_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line.field",
        inverse_name="cnab_line_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    group_ids = fields.One2many(
        comodel_name="cnab.line.field.group",
        inverse_name="cnab_line_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    batch_id = fields.Many2one(
        comodel_name="l10n_br_cnab.batch",
        ondelete="cascade",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        ondelete="cascade",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.model
    def _selection_target_model(self):
        return [
            ("account.payment.order", "Payment Order"),
            ("account.payment.line", "Payment Line"),
        ]

    resource_ref = fields.Reference(
        string="Reference",
        selection="_selection_target_model",
        states={"draft": [("readonly", False)]},
    )

    cnab_format = fields.Char(
        related="cnab_structure_id.cnab_format",
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    cnab_payment_way_ids = fields.Many2many(
        comodel_name="cnab.payment.way",
        string="Payments Ways",
        help="Payment Ways that must use this segment.",
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def is_requerid(self, payment_way):
        """
        checks if the segment is required based on the information provided.
        """
        self.ensure_one()
        if self.requerid:
            return True
        return payment_way in self.cnab_payment_way_ids

    def _compute_content_source_model_id(self):
        if self.type in ["header", "trailer"]:
            self.content_source_model_id = self.env["ir.model"].search(
                [("model", "=", "account.payment.order")]
            )
        else:
            self.content_source_model_id = self.env["ir.model"].search(
                [("model", "=", "account.payment.line")]
            )

    def _compute_dest_source_model_id(self):
        if self.type in ["header", "trailer"] and not self.batch_id:
            self.content_dest_model_id = self.env["ir.model"].search(
                [("model", "=", "l10n_br_cnab.return.log")]
            )
        elif self.type in ["header", "trailer"] and self.batch_id:
            self.content_dest_model_id = self.env["ir.model"].search(
                [("model", "=", "l10n_br_cnab.return.lot")]
            )
        else:
            self.content_dest_model_id = self.env["ir.model"].search(
                [("model", "=", "l10n_br_cnab.return.event")]
            )

    def output(self, resource_ref, record_type, **kwargs):
        "Compute CNAB output with all fields for this Line"
        self.ensure_one()
        line = CnabLine(record_type)

        def add_field(field_id):
            name, value = field_id.output(resource_ref, **kwargs)
            line.add_field(name=name, value=value, pos=field_id.start_pos)

        fields_without_group = self.field_ids.filtered(lambda x: not x.cnab_group_id)
        for field_id in fields_without_group:
            # we added the basic fields first (no group)
            # as they can be used as a condition in a group.
            add_field(field_id)
        fields_with_group = self.field_ids.filtered(lambda x: x.cnab_group_id)
        for field_id in fields_with_group:
            # skips inserting the field if it does not meet the group condition.
            conditions = field_id.cnab_group_id.condition_ids
            skip = False
            for cond in conditions:
                field_key = cond.field_id.ref_name
                field_value = line.get_field_by_name(field_key).value
                cond_values = json.loads(cond.json_value)
                if cond.operator == "in":
                    cond_result = field_value in cond_values
                if cond.operator == "not in":
                    cond_result = field_value not in cond_values
                if not cond_result:
                    skip = True
                    break
            if skip:
                continue
            add_field(field_id)
        return line

    @api.depends("segment_code", "cnab_structure_id", "cnab_structure_id.name", "type")
    def _compute_name(self):
        for line in self:
            if line.type == "segment":
                name = f"{line.type} {line.segment_code}"
            else:
                name = line.type

            if line.batch_id:
                line.name = (
                    f"{line.cnab_structure_id.name} -> {line.batch_id.name} -> {name}"
                )
            else:
                line.name = f"{line.cnab_structure_id.name} -> {name}"

    def unlink(self):
        lines = self.filtered(lambda line: line.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Line which is not draft !"))
        return super().unlink()

    def check_line(self):
        cnab_fields = self.field_ids.sorted(key=lambda r: r.start_pos)

        if len(cnab_fields) == 0:
            raise UserError(
                _(f"{self.name}: The cnab line must have some cnab field defined.")
            )

        for f in cnab_fields:
            f.check_field()

        if cnab_fields[0].start_pos != 1:
            raise UserError(
                _(f"{self.name}: The start position of first field must be 1.")
            )

        last_pos = int(self.cnab_structure_id.cnab_format)
        if cnab_fields[-1].end_pos != last_pos:
            raise UserError(
                _(f"{self.name}: the end position of last field is not {last_pos}.")
            )

        if self.batch_id and self.batch_id.cnab_structure_id != self.cnab_structure_id:
            raise UserError(
                _(
                    f"{self.name}: line cnab structure is different of batch cnab"
                    " structure."
                )
            )

    @api.onchange("communication_flow")
    def _onchange_communication_flow(self):
        self.current_view = "general"

    def action_general_view(self):
        self.current_view = "general"

    def action_sending_view(self):
        self.current_view = "sending"

    def action_return_view(self):
        self.current_view = "return"
