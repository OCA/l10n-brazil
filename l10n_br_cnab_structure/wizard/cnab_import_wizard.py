# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from io import StringIO
import base64


class CNABImportWizard(models.TransientModel):

    _name = "cnab.import.wizard"
    _description = "CNAB Import Wizard"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        help="Only journals where the CNAB Import is allowed.",
        required=True,
    )
    bank_account_cnab_id = fields.Many2one(
        comodel_name="account.account",
        related="journal_id.default_account_id",
        readonly=True,
    )
    return_file = fields.Binary("Return File")
    filename = fields.Char()
    type = fields.Selection(
        [
            ("inbound", "Inbound Payment"),
            ("outbound", "Outbound Payment"),
        ],
        string="Type",
    )

    bank_id = fields.Many2one(comodel_name="res.bank", related="journal_id.bank_id")
    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method", compute="_compute_payment_method_ids"
    )
    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        domain="[('bank_id', '=', bank_id),('payment_method_id', 'in', payment_method_ids),('state', '=', 'approved')]",
    )
    cnab_format = fields.Char(
        related="cnab_structure_id.cnab_format",
    )

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        structure_obj = self.env["l10n_br_cnab.structure"]
        structure_ids = structure_obj.search(
            [
                ("bank_id", "=", self.bank_id.id),
                ("payment_method_id", "in", self.payment_method_ids.ids),
                ("state", "=", "approved"),
            ]
        )
        if len(structure_ids):
            self.cnab_structure_id = structure_ids[0]
        else:
            self.cnab_structure_id = [(5, 0, 0)]

    @api.depends("journal_id", "type")
    def _compute_payment_method_ids(self):
        for record in self:
            if record.type == "inbound":
                record.payment_method_ids = record.journal_id.inbound_payment_method_ids
            elif record.type == "outbound":
                record.payment_method_ids = (
                    record.journal_id.outbound_payment_method_ids
                )
            else:
                record.payment_method_ids = [(5, 0, 0)]

    def _get_conf_positions_240(self):
        structure_id = self.cnab_structure_id
        start_pos = {
            "bank": structure_id.conf_bank_start_pos - 1,
            "batch": structure_id.conf_batch_start_pos - 1,
            "record_type": structure_id.conf_record_type_start_pos - 1,
            "segment": structure_id.conf_detail_segment_start_pos - 1,
            "payment_way": structure_id.conf_payment_way_start_pos - 1,
        }
        end_pos = {
            "bank": structure_id.conf_bank_end_pos,
            "batch": structure_id.conf_batch_end_pos,
            "record_type": structure_id.conf_record_type_end_pos,
            "segment": structure_id.conf_detail_segment_end_pos,
            "payment_way": structure_id.conf_payment_way_end_pos,
        }
        return start_pos, end_pos

    def _get_record_type(self):
        structure_id = self.cnab_structure_id
        record_type = {
            "header_file": structure_id.record_type_file_header_id,
            "trailer_file": structure_id.record_type_file_trailer_id,
            "header_batch": structure_id.record_type_batch_header_id,
            "trailer_batch": structure_id.record_type_batch_trailer_id,
            "detail": structure_id.record_type_detail_id,
        }
        return record_type

    def _get_content(self, line, field):
        start_pos, end_pos = self._get_conf_positions_240()
        return line[start_pos[field] : end_pos[field]]

    def _get_lines_from_file(self, file):
        file = base64.b64decode(self.return_file)
        string = StringIO(file.decode("utf-8"))
        lines = string.readlines()
        return lines

    def _check_bank(self, line):
        bank_line = self._get_content(line, "bank")
        bank_structure = self.cnab_structure_id.bank_id.code_bc
        if bank_line != bank_structure:
            raise UserError(
                _(
                    f"The bank {bank_line} from file is different of the bank os selected structure({bank_structure})."
                )
            )

    def _filter_lines_from_type(self, lines, type_name):
        record_type = self._get_record_type()
        filtered_lines = list(
            filter(
                lambda line: self._get_content(line, "record_type")
                == str(record_type[type_name]),
                lines,
            )
        )
        return filtered_lines

    def _get_unique_batch_list(self, lines):
        batch_list = []
        for line in lines:
            batch = self._get_content(line, "batch")
            # Ignore batches from header and trailer of file, they will always be 0000 and 9999.
            # If there is an exception, it must be handled.
            if batch not in ["0000", "9999"]:
                batch_list.append(batch)
        return list(set(batch_list))

    def _get_batches(self, lines):
        batch_list = self._get_unique_batch_list(lines)
        batches = {}
        for batch in batch_list:
            pass

    def _import_cnab_240(self):
        lines = self._get_lines_from_file(self.return_file)
        self._check_bank(lines[0])
        header_file_line = self._filter_lines_from_type(lines, "header_file")
        trailer_file_line = self._filter_lines_from_type(lines, "trailer_file")
        batches = self._get_batches(lines)

        pass

    def import_cnab(self):
        if self.cnab_format == "240":
            self._import_cnab_240()
        else:
            raise UserError(_(f"CNAB Format {self.cnab_format} not implemented."))
