# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CNABBatch(models.Model):

    _name = "l10n_br_cnab.batch"
    _description = "A batch of lines in a CNAB structure."

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line",
        inverse_name="batch_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    def get_header(self):
        "Returns the batch header record"
        return self.line_ids.filtered(lambda l: l.type == "header")

    def get_trailer(self):
        "Returns the batch trailer record"
        return self.line_ids.filtered(lambda l: l.type == "trailer")

    def get_segments(self):
        "Returns the batch segments records"
        return self.line_ids.filtered(lambda l: l.type == "segment")

    def output(self, pay_order, batch_sequence):
        """Return a batch output"""
        batch_lines = []
        batch_lines.append(
            self.get_header().output(
                pay_order, seq_batch=batch_sequence, batch_lines=batch_lines
            )
        )
        for count, bank_line in enumerate(pay_order.bank_line_ids, 1):
            for segment in self.get_segments():
                batch_lines.append(
                    segment.output(
                        bank_line,
                        seq_batch=batch_sequence,
                        seq_record_detail=count,
                        batch_lines=batch_lines,
                    )
                )
        batch_lines.append(
            self.get_trailer().output(
                pay_order,
                seq_batch=batch_sequence,
                qty_records=len(batch_lines) + 1,
                batch_lines=batch_lines,
            )
        )
        return batch_lines

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

        if self.cnab_structure_id.cnab_format != "240":
            raise UserError(
                _(f"{self.name}: A batch must belong to a CNAB 240 structure!")
            )

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
        structure_lines = self.cnab_structure_id.line_ids.sorted(
            key=lambda f: f.sequence
        ).ids
        first_line = structure_lines.index(batch_lines[0])
        last_line = first_line + len(batch_lines)
        structure_lines = structure_lines[first_line:last_line]

        if batch_lines != structure_lines:
            raise UserError(
                _(f"Batch {self.name}: The lines of batch must be together!")
            )
