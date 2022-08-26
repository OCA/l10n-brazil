# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import yaml

from email.policy import default
from ..cnab.cnab import Cnab, RecordType
from odoo import _, api, fields, models
from odoo.exceptions import UserError

CNAB_CODES = ["240", "400", "500", "750"]


class CNABStructure(models.Model):

    _name = "l10n_br_cnab.structure"
    _description = (
        "An structure with header, body and trailer that make up the CNAB structure."
    )

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})

    bank_id = fields.Many2one(
        comodel_name="res.bank", readonly=True, states={"draft": [("readonly", False)]}
    )

    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        states={"draft": [("readonly", False)]},
        domain=[("code", "in", CNAB_CODES)],
    )

    cnab_format = fields.Char(
        related="payment_method_id.code",
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

    def output_dicts(self, pay_order):
        """Receives a Payment Order record and returns a list of dicts,
        each dict represents a line from the CNAB file."""
        cnab = Cnab()
        cnab.header = self.get_header().output(pay_order, RecordType.HEADER)
        batch_template_id = pay_order.payment_mode_id.cnab_batch_id
        if batch_template_id:
            batch = batch_template_id.output(pay_order, 1, "1")
            cnab.batches.append(batch)
        cnab.trailer = self.get_trailer().output(
            pay_order,
            RecordType.TRAILER,
            cnab=cnab,
        )
        return cnab

    def output_yaml(self, pay_order):
        """Receives a Payment Order record and returns the data in the CNAB structure
        in YAML format."""
        cnab = self.output_dicts(pay_order)
        return yaml.dump(
            [line.asdict() for line in cnab.lines()],
            sort_keys=False,
        )

    def output(self, pay_order):
        """Receives a Payment Order record and returns the data in the CNAB structure"""
        cnab = self.output_dicts(pay_order)
        return cnab.output()

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

        if not self.payment_method_id:
            raise UserError(_(f"{self.name}: Payment Method not found."))

        if self.cnab_format not in CNAB_CODES:
            raise UserError(
                _(f"{self.name}: The code of payment method must be {CNAB_CODES}")
            )

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

        if not self.bank_id:
            raise UserError(_(f"{self.name}: A CNAB Structure need to have a bank!"))
