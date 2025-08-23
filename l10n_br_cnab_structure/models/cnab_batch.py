# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..cnab.cnab import CnabBatch, CnabDetailRecord, RecordType


class CNABBatch(models.Model):
    _name = "l10n_br_cnab.batch"
    _description = "A batch of lines in a CNAB structure."

    name = fields.Char(readonly=True, states={"draft": [("readonly", False)]})

    cnab_structure_id = fields.Many2one(
        help="Only structures with code equal to 240 is allowed.",
        comodel_name="l10n_br_cnab.structure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    line_ids = fields.One2many(
        help="Only structures with code equal to 240 is allowed.",
        comodel_name="l10n_br_cnab.line",
        inverse_name="batch_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    cnab_payment_way_ids = fields.One2many(
        comodel_name="cnab.payment.way",
        string="Payments Ways",
        inverse_name="batch_id",
        help="Payments ways that use the structure of this batch.",
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    def get_header(self):
        "Returns the batch header record"
        return self.line_ids.filtered(lambda line: line.type == "header")

    def get_trailer(self):
        "Returns the batch trailer record"
        return self.line_ids.filtered(lambda line: line.type == "trailer")

    def get_segments(self):
        "Returns the batch segments records"
        return self.line_ids.filtered(lambda line: line.type == "segment")

    def output(self, bank_lines, seq_batch):
        """
        Generates and returns a batch object with the cnab output data.
        """
        pay_order = bank_lines[0].order_id
        payment_way_id = bank_lines[0].cnab_payment_way_id
        type_code = bank_lines[0].service_type
        batch = CnabBatch()
        # Initialize the counter for seq_record_detail
        seq_record_detail_counter = 0

        # HEADER
        batch.header = self.get_header().output(
            pay_order,
            RecordType.HEADER_BATCH,
            seq_batch=seq_batch,
            payment_way_code=payment_way_id.code,
            payment_type_code=type_code,
        )

        # DETAIL RECORDS

        for count, bank_line in enumerate(bank_lines, 1):
            detail_record = CnabDetailRecord(name=str(count))
            # Determine the base seq_record_detail value for this bank_line iteration
            current_record_detail_seq = count
            for segment_t in self.get_segments():
                if segment_t.is_requerid(payment_way_id):
                    if self.cnab_structure_id.unique_seq_per_segment:
                        seq_record_detail_counter += 1
                    segment_seq_detail = (
                        seq_record_detail_counter
                        if self.cnab_structure_id.unique_seq_per_segment
                        else current_record_detail_seq
                    )

                    segment = segment_t.output(
                        bank_line,
                        RecordType.DETAIL_RECORD,
                        seq_batch=seq_batch,
                        seq_record_detail=segment_seq_detail,
                    )
                    detail_record.segments.append(segment)
            batch.detail_records.append(detail_record)

        # TRAILER
        batch.trailer = self.get_trailer().output(
            pay_order,
            RecordType.TRAILER_BATCH,
            seq_batch=seq_batch,
            qty_records=batch.len_records(),
            batch_detail_lines=batch.detail_lines(),
        )
        return batch

    def unlink(self):
        lines = self.filtered(lambda line: line.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Batch which is not draft !"))
        return super().unlink()

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
                    f"Batch {self.name}: Every Batch need to have at least one segment"
                    " line!"
                )
            )

        if len(header_line) != 1:
            raise UserError(
                _(
                    f"Batch {self.name}: One batch need to have one and only one"
                    " header line!"
                )
            )

        if len(trailer_line) != 1:
            raise UserError(
                _(
                    f"Batch {self.name}: One batch need to have one and only one"
                    " trailer line!"
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
