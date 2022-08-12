# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CNABBatch(models.Model):

    _name = "l10n_br_cnab.batch"
    _description = "A batch of lines in a CNAB file."

    name = fields.Char(readonly=True, states={"draft": [("readonly", "=", False)]})

    cnab_file_id = fields.Many2one(
        comodel_name="l10n_br_cnab.file",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line",
        inverse_name="batch_id",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    def unlink(self):
        lines = self.filtered(lambda l: l.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Batch which is not draft !"))
        return super(CNABBatch, self).unlink()

    def check_batch(self):

        if self.cnab_file_id.cnab_format != "240":
            raise UserError(_(f"{self.name}: A batch must belong to a CNAB 240 file!"))

        segment_lines = self.line_ids.filtered(lambda b: b.type == "segment")
        header_line = self.line_ids.filtered(lambda b: b.type == "header")
        trailer_line = self.line_ids.filtered(lambda b: b.type == "trailer")

        if not segment_lines:
            raise UserError(
                _(
                    f"Batch {self.name}: Every Batch need to have at least one segment line!"
                )
            )

        if len(header_line) != 1:
            raise UserError(
                _(
                    f"Batch {self.name}: One batch need to have one and only one header line!"
                )
            )

        if len(trailer_line) != 1:
            raise UserError(
                _(
                    f"Batch {self.name}: One batch need to have one and only one trailer line!"
                )
            )

        batch_lines = self.line_ids.sorted(key=lambda b: b.sequence)

        if batch_lines[0].type != "header":
            raise UserError(
                _(f"Batch {self.name}: The first line need to be a header!")
            )

        if batch_lines[-1].type != "trailer":
            raise UserError(
                _(f"Batch {self.name}: The last line need to be a trailer!")
            )

        batch_lines = batch_lines.ids
        file_lines = self.cnab_file_id.line_ids.sorted(key=lambda f: f.sequence).ids
        first_line = file_lines.index(batch_lines[0])
        last_line = first_line + len(batch_lines)
        file_lines = file_lines[first_line:last_line]

        if batch_lines != file_lines:
            raise UserError(
                _(f"Batch {self.name}: The lines of batch must be together!")
            )
