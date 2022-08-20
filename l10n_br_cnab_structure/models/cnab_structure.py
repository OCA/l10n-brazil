# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from email.policy import default
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CNABStructure(models.Model):

    _name = "l10n_br_cnab.structure"
    _description = (
        "An structure with header, body and trailer that make up the CNAB structure."
    )

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})

    cnab_format = fields.Selection(
        selection=[("240", "240"), ("400", "400")],
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    batch_ids = fields.One2many(
        comodel_name="l10n_br_cnab.batch",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    content_source_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Content Source",
        help="Related model that will provide the origin of the contents of CNAB files.",
        compute="_compute_content_source_model_id",
    )

    def get_header(self):
        "Returns the file header record"
        return self.line_ids.filtered(lambda l: l.type == "header" and not l.batch_id)

    def get_trailer(self):
        "Returns the file trailer record"
        return self.line_ids.filtered(lambda l: l.type == "trailer" and not l.batch_id)

    def output(self, pay_order):
        """Generete CNAB Output"""
        lines = []
        lines.append(self.get_header().output(pay_order))
        batch_id = pay_order.payment_mode_id.cnab_batch_id
        if batch_id:
            lines.extend(batch_id.output(pay_order, 1))
        lines.append(self.get_trailer().output(pay_order))
        return "\n".join(lines)

    def _compute_content_source_model_id(self):
        self.content_source_model_id = self.env["ir.model"].search(
            [("model", "=", "account.payment.order")]
        )

    def unlink(self):
        lines = self.filtered(lambda l: l.state != "draft")
        if lines:
            raise UserError(
                _("You cannot delete an CNAB Structure which is not draft !")
            )
        return super(CNABStructure, self).unlink()

    def action_review(self):
        self.check_structure()
        self.line_ids.field_ids.write({"state": "review"})
        self.line_ids.batch_id.write({"state": "review"})
        self.line_ids.write({"state": "review"})
        self.write({"state": "review"})

    def action_approve(self):
        self.line_ids.field_ids.write({"state": "approved"})
        self.line_ids.batch_id.write({"state": "approved"})
        self.line_ids.write({"state": "approved"})
        self.write({"state": "approved"})

    def action_draft(self):
        self.line_ids.field_ids.write({"state": "draft"})
        self.line_ids.batch_id.write({"state": "draft"})
        self.line_ids.write({"state": "draft"})
        self.write({"state": "draft"})

    def check_structure(self):

        for l in self.line_ids:
            l.check_line()

        for l in self.batch_ids:
            l.check_batch()

        segment_lines = self.line_ids.filtered(
            lambda l: l.type == "segment" and not l.batch_id
        )
        header_line = self.line_ids.filtered(
            lambda l: l.type == "header" and not l.batch_id
        )
        trailer_line = self.line_ids.filtered(
            lambda l: l.type == "trailer" and not l.batch_id
        )

        if segment_lines and self.cnab_format == "240":
            raise UserError(
                _(f"{self.name}: CNAB 240 structures can't have segment lines!")
            )

        if not segment_lines and self.cnab_format == "400":
            raise UserError(
                _(f"{self.name}: CNAB 400  structures need to have segment lines!")
            )

        if len(header_line) != 1:
            raise UserError(
                _(f"{self.name}: Structures need to have one and only one header line!")
            )

        if len(trailer_line) != 1:
            raise UserError(
                _(
                    f"{self.name}: Structures need to have one and only one trailer line!"
                )
            )

        if self.cnab_format == "240" and not self.batch_ids:
            raise UserError(
                _(f"{self.name}: CNAB 240 structures need to have at least 1 batch!")
            )

        lines = self.line_ids.sorted(key=lambda b: b.sequence)

        if lines[0].type != "header":
            raise UserError(_(f"{self.name}: The first line need to be a header!"))

        if lines[-1].type != "trailer":
            raise UserError(_(f"{self.name}: The last line need to be a trailer!"))
