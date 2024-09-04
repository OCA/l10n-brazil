# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import yaml

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..cnab.cnab import Cnab, RecordType

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

    payment_type = fields.Selection(
        related="payment_method_id.payment_type",
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
        help="Related model that will provide the origin of the contents of CNAB"
        " files.",
        compute="_compute_content_source_model_id",
    )

    conf_bank_start_pos = fields.Integer(
        string="Bank Start Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_bank_end_pos = fields.Integer(
        string="Bank Last Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_record_type_start_pos = fields.Integer(
        string="Record Type Start Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_record_type_end_pos = fields.Integer(
        string="Record Type Last Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_batch_start_pos = fields.Integer(
        string="Batch Start Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_batch_end_pos = fields.Integer(
        string="Batch Last Position",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_payment_way_start_pos = fields.Integer(
        help="Payment Way start position in Header Batch Records."
        " Only for Header Batch Records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_payment_way_end_pos = fields.Integer(
        help="Payment Way last position in Header Batch Records."
        " Only for Header Batch Records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_detail_start_pos = fields.Integer(
        help="Position of sequencial identification of Detail Records."
        " Only for detail records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_detail_end_pos = fields.Integer(
        help="Last position of sequencial identification of Detail Records."
        " Only for detail records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_segment_start_pos = fields.Integer(
        help="Start position of segment of an detail record. Only for detail"
        " records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    conf_segment_end_pos = fields.Integer(
        help="Last position of segment of an detail record. Only for detail"
        " records.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    record_type_file_header_id = fields.Integer(
        string="File Header Type ID",
        help="What`s the identification for header of file type?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    record_type_file_trailer_id = fields.Integer(
        string="File Trailer Type ID",
        help="What`s the identification for trailer of file type?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    record_type_batch_header_id = fields.Integer(
        string="Batch Header Type ID",
        help="What`s the identification for header of batch type?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    record_type_batch_trailer_id = fields.Integer(
        string="Batch Trailer Type ID",
        help="What`s the identification for trailer of batch type?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    record_type_detail_id = fields.Integer(
        string="Detail Type ID",
        help="What`s the identification for detail type?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_payment_way_ids = fields.One2many(
        comodel_name="cnab.payment.way",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_pix_key_type_ids = fields.One2many(
        comodel_name="cnab.pix.key.type",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_pix_transfer_type_ids = fields.One2many(
        comodel_name="cnab.pix.transfer.type",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_occurrence_ids = fields.One2many(
        comodel_name="cnab.occurrence",
        inverse_name="cnab_structure_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("cnab_format", "payment_type")
    def _onchange_cnab_format(self):
        if self.cnab_format == "240":
            # Default Configuration Fields
            self.conf_bank_start_pos = 1
            self.conf_bank_end_pos = 3
            self.conf_record_type_start_pos = 8
            self.conf_record_type_end_pos = 8
            self.conf_batch_start_pos = 4
            self.conf_batch_end_pos = 7
            if self.payment_type == "outbound":
                self.conf_payment_way_start_pos = 12
                self.conf_payment_way_end_pos = 13
            else:
                self.conf_payment_way_start_pos = None
                self.conf_payment_way_end_pos = None
            self.conf_detail_start_pos = 9
            self.conf_detail_end_pos = 13
            self.conf_segment_start_pos = 14
            self.conf_segment_end_pos = 14

            # Default Record Types
            self.record_type_file_header_id = 0
            self.record_type_file_trailer_id = 9
            self.record_type_batch_header_id = 1
            self.record_type_batch_trailer_id = 5
            self.record_type_detail_id = 3

        elif self.cnab_format == "400":
            # Default Configuration Fields
            self.conf_bank_start_pos = None
            self.conf_bank_end_pos = None
            self.conf_record_type_start_pos = 8
            self.conf_record_type_end_pos = 8
            self.conf_batch_start_pos = None
            self.conf_batch_end_pos = None
            self.conf_payment_way_start_pos = None
            self.conf_payment_way_end_pos = None
            self.conf_detail_start_pos = None
            self.conf_detail_end_pos = None
            self.conf_segment_start_pos = None
            self.conf_segment_end_pos = None

            # Default Record Types
            self.record_type_file_header_id = 0
            self.record_type_file_trailer_id = 9
            self.record_type_batch_header_id = None
            self.record_type_batch_trailer_id = None
            self.record_type_detail_id = 1
        else:
            # Default Configuration Fields
            self.conf_bank_start_pos = None
            self.conf_bank_end_pos = None
            self.conf_record_type_start_pos = None
            self.conf_record_type_end_pos = None
            self.conf_batch_start_pos = None
            self.conf_batch_end_pos = None
            self.conf_payment_way_start_pos = None
            self.conf_payment_way_end_pos = None
            self.conf_detail_start_pos = None
            self.conf_detail_end_pos = None
            self.conf_segment_start_pos = None
            self.conf_segment_end_pos = None

            # Default Record Types
            self.record_type_file_header_id = None
            self.record_type_file_trailer_id = None
            self.record_type_batch_header_id = None
            self.record_type_batch_trailer_id = None
            self.record_type_detail_id = None

    def get_header(self):
        "Returns the file header record"
        return self.line_ids.filtered(
            lambda line: line.type == "header" and not line.batch_id
        )

    def get_trailer(self):
        "Returns the file trailer record"
        return self.line_ids.filtered(
            lambda line: line.type == "trailer" and not line.batch_id
        )

    def output_dicts(self, pay_order):
        """
        Receives a Payment Order record and returns a Cnab Data Object"
        """
        cnab = Cnab()

        # HEADER
        cnab.header = self.get_header().output(pay_order, RecordType.HEADER)

        # BATCHES
        grouped_bank_lines = {}
        for bline in pay_order.payment_line_ids:
            way_code = bline.cnab_payment_way_id.code
            type_code = bline.service_type
            batch_key = tuple([way_code, type_code])
            grouped_bank_lines[batch_key] = grouped_bank_lines.get(batch_key, [])
            grouped_bank_lines[batch_key].append(bline)
        for count, bank_lines in enumerate(grouped_bank_lines.values(), 1):
            batch_template_id = bank_lines[0].batch_template_id
            batch = batch_template_id.output(bank_lines, count)
            cnab.batches.append(batch)

        # TRAILER
        cnab.trailer = self.get_trailer().output(
            pay_order,
            RecordType.TRAILER,
            qty_batches=cnab.len_batches(),
            qty_records=cnab.len_records(),
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
        lines = self.filtered(lambda line: line.state != "draft")
        if lines:
            raise UserError(
                _("You cannot delete an CNAB Structure which is not draft !")
            )
        return super().unlink()

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
        for line in self.line_ids:
            line.check_line()

        for batch in self.batch_ids:
            batch.check_batch()

        if not self.payment_method_id:
            raise UserError(_(f"{self.name}: Payment Method not found."))

        if self.cnab_format not in CNAB_CODES:
            raise UserError(
                _(f"{self.name}: The code of payment method must be {CNAB_CODES}")
            )

        segment_lines = self.line_ids.filtered(
            lambda line: line.type == "segment" and not line.batch_id
        )
        header_line = self.line_ids.filtered(
            lambda line: line.type == "header" and not line.batch_id
        )
        trailer_line = self.line_ids.filtered(
            lambda line: line.type == "trailer" and not line.batch_id
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
                    f"{self.name}: Structures need to have one and only one trailer"
                    " line!"
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

        positions = [
            self.conf_bank_start_pos,
            self.conf_bank_end_pos,
            self.conf_record_type_start_pos,
            self.conf_record_type_end_pos,
            self.conf_batch_start_pos,
            self.conf_batch_end_pos,
            self.conf_payment_way_start_pos,
            self.conf_payment_way_end_pos,
            self.conf_detail_start_pos,
            self.conf_detail_end_pos,
            self.conf_segment_start_pos,
            self.conf_segment_end_pos,
        ]

        last_position = int(self.cnab_format)
        for f in positions:
            if f is not None and f < 1 or f > last_position:
                raise UserError(
                    _(
                        f"{self.name}: All the configuration fields positions "
                        f"need to be between 1 and {last_position}!"
                    )
                )
