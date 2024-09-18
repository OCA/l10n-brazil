# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
from io import StringIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    return_file = fields.Binary()
    filename = fields.Char()
    type = fields.Selection(
        [
            ("inbound", "Inbound Payment"),
            ("outbound", "Outbound Payment"),
        ],
    )

    bank_id = fields.Many2one(comodel_name="res.bank", related="journal_id.bank_id")
    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method", compute="_compute_payment_method_ids"
    )
    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        domain="[('bank_id', '=', bank_id),('payment_method_id', "
        "'in', payment_method_ids),('state', '=', 'approved')]",
    )
    cnab_format = fields.Char(
        related="cnab_structure_id.cnab_format",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),
    )

    @api.model
    def _default_company_id(self):
        return self.env.company

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
        """
        Return Start and End position of configuration files.
        Values pre defined: bank, record_type, batch, payment_way, detail or segment.
        """
        structure_id = self.cnab_structure_id
        start_pos = {
            "bank": structure_id.conf_bank_start_pos - 1,
            "record_type": structure_id.conf_record_type_start_pos - 1,
            "batch": structure_id.conf_batch_start_pos - 1,
            "payment_way": structure_id.conf_payment_way_start_pos - 1,
            "detail": structure_id.conf_detail_start_pos - 1,
            "segment": structure_id.conf_segment_start_pos - 1,
        }
        end_pos = {
            "bank": structure_id.conf_bank_end_pos,
            "record_type": structure_id.conf_record_type_end_pos,
            "batch": structure_id.conf_batch_end_pos,
            "payment_way": structure_id.conf_payment_way_end_pos,
            "detail": structure_id.conf_detail_end_pos,
            "segment": structure_id.conf_segment_end_pos,
        }
        return start_pos, end_pos

    def _get_record_types(self):
        structure_id = self.cnab_structure_id
        record_types = {
            "header_file": structure_id.record_type_file_header_id,
            "trailer_file": structure_id.record_type_file_trailer_id,
            "header_batch": structure_id.record_type_batch_header_id,
            "trailer_batch": structure_id.record_type_batch_trailer_id,
            "detail": structure_id.record_type_detail_id,
        }
        return record_types

    def _get_content(self, line, conf_field):
        """
        Get content of configuration field from CNAB line.
        Values pre defined: bank, record_type, batch, payment_way, detail or segment.
        """
        start_pos, end_pos = self._get_conf_positions_240()
        return line[start_pos[conf_field] : end_pos[conf_field]]

    def _get_lines_from_file(self, file):
        file = base64.b64decode(self.return_file)
        string = StringIO(file.decode("utf-8"))
        lines = string.readlines()
        # Remove special character at the end of the line.
        lines = [line.replace("\r", "").replace("\n", "") for line in lines]
        return lines

    def _check_bank(self, line):
        bank_line = self._get_content(line, "bank")
        bank_structure = self.cnab_structure_id.bank_id.code_bc
        if bank_line != bank_structure:
            raise UserError(
                _(
                    f"The bank {bank_line} from file is different of "
                    f"the bank os selected structure({bank_structure})."
                )
            )

    def _check_cnab_240(self, lines):
        for index, line in enumerate(lines):
            if len(line) != 240:
                raise UserError(
                    _(f"Number of positions of line {index+1} is different of 240.")
                )

    def _filter_lines(self, lines, conf_field, value):
        """
        Returns CNAB lines filtered by specific values of a configuration field.
        This fields are set in cnab structure.

        Args:
            lines (List): A list of strings of CNAB lines.
            conf_field (string): The name of the configuration field:
                bank, record_type, batch, payment_way, detail or segment.
            value (string, int): The value of conf_field to filter.
        Returns:
            List: A list of CNAB lines.
        """
        filtered_lines = list(
            filter(
                lambda line: self._get_content(line, conf_field) == str(value),
                lines,
            )
        )
        return filtered_lines

    def _filter_lines_from_type(self, lines, type_name):
        """
        Returns CNAB lines filtered by type. This types are set in cnab structure.

        Args:
            lines (List): A list of strings of CNAB lines.
            type_name (string): Name of type:
                header_file, trailer_file, header_batch, trailer_batch or detail.
        Returns:
            List: A list of CNAB lines.
        """
        record_types = self._get_record_types()
        filtered_lines = self._filter_lines(
            lines, "record_type", record_types[type_name]
        )

        return filtered_lines

    def _get_unique_batch_list(self, lines):
        batch_list = []
        for line in lines:
            batch = self._get_content(line, "batch")
            # Ignore batches from header and trailer of file,
            # they will always be 0000 and 9999.
            # If there is an exception, it must be handled.
            if batch not in ["0000", "9999"]:
                batch_list.append(batch)
        return list(set(batch_list))

    def _get_unique_datail_list(self, lines):
        detail_list = []
        for line in lines:
            detail = self._get_content(line, "detail")
            detail_list.append(detail)
        return list(set(detail_list))

    def _get_segments(self, segment_lines, batch_template):
        segments = []
        for s in segment_lines:
            segment_code = self._get_content(s, "segment")
            line_template = batch_template.line_ids.filtered(
                lambda line, segment_code=segment_code: line.type == "segment"
                and line.segment_code == segment_code
            )
            segment = {"raw_line": s, "line_template": line_template}
            segments.append(segment)
        return segments

    def _get_details(self, detail_lines, batch_template):
        detail_list = self._get_unique_datail_list(detail_lines)
        details = []

        for d in detail_list:
            segment_lines = self._filter_lines(detail_lines, "detail", d)
            segments = self._get_segments(segment_lines, batch_template)
            details.append(segments)

        return details

    def _get_payment_way(self, code):
        batch_domain = [
            ("cnab_structure_id", "=", self.cnab_structure_id.id),
            ("code", "=", code),
        ]
        return self.env["cnab.payment.way"].search(batch_domain, limit=1)

    def _get_batch_template(self, payment_way_code):
        cnab_payment_way_id = self._get_payment_way(payment_way_code)
        batch_domain = [
            ("cnab_structure_id", "=", self.cnab_structure_id.id),
            ("cnab_payment_way_ids", "in", [cnab_payment_way_id.id]),
        ]
        return self.env["l10n_br_cnab.batch"].search(batch_domain, limit=1)

    def _get_batches(self, lines):
        batch_list = self._get_unique_batch_list(lines)
        batches = []

        for b in batch_list:
            batch = {}
            batch_lines = self._filter_lines(lines, "batch", b)

            batch_header_raw_line = self._filter_lines_from_type(
                batch_lines, "header_batch"
            )[0]
            payment_way_code = self._get_content(batch_header_raw_line, "payment_way")
            batch_template = self._get_batch_template(payment_way_code)

            batch["header_batch_line"] = {
                "raw_line": batch_header_raw_line,
                "line_template": batch_template.line_ids.filtered(
                    lambda line: line.type == "header"
                ),
            }
            batch["trailer_batch_line"] = {
                "raw_line": self._filter_lines_from_type(batch_lines, "trailer_batch")[
                    0
                ],
                "line_template": batch_template.line_ids.filtered(
                    lambda line: line.type == "trailer"
                ),
            }

            detail_lines = self._filter_lines_from_type(batch_lines, "detail")
            batch["details"] = self._get_details(detail_lines, batch_template)

            batches.append(batch)

        return batches

    def _get_data_from_file(self):
        lines = self._get_lines_from_file(self.return_file)
        self._check_bank(lines[0])
        self._check_cnab_240(lines)
        data = {}
        data["header_file_line"] = {
            "raw_line": self._filter_lines_from_type(lines, "header_file")[0],
            "line_template": self.cnab_structure_id.line_ids.filtered(
                lambda line: not line.batch_id and line.type == "header"
            ),
        }
        data["trailer_file_line"] = {
            "raw_line": self._filter_lines_from_type(lines, "trailer_file")[0],
            "line_template": self.cnab_structure_id.line_ids.filtered(
                lambda line: not line.batch_id and line.type == "trailer"
            ),
        }
        data["batches"] = self._get_batches(lines)
        return data

    def _parse_value(self, value, fld):
        if fld.type == "num":
            if fld.assumed_comma > 0:
                value = float(value) / (10**fld.assumed_comma)
            else:
                value = int(value)
        if fld.type == "alpha":
            value = value.strip()
        return value

    def _get_dict_value_from_line(self, data_line):
        value_dict = {}
        if data_line["line_template"]:
            for fld in data_line["line_template"].field_ids:
                if fld.content_dest_field:
                    value = data_line["raw_line"][fld.start_pos - 1 : fld.end_pos]
                    if fld.return_dynamic_content:
                        value = fld.eval_compute_value(
                            value, fld.return_dynamic_content
                        )
                    else:
                        value = self._parse_value(value, fld)
                    value_dict[fld.content_dest_field] = value

        return value_dict

    def _create_return_events(self, details, return_lot_id, return_log_id):
        return_event_obj = self.env["l10n_br_cnab.return.event"]

        for detail in details:
            event_value_dict = {}
            template_not_implemented = False
            for segment in detail:
                event_value_dict.update(self._get_dict_value_from_line(segment))
                if not segment["line_template"]:
                    template_not_implemented = True
            if template_not_implemented:
                event_value_dict["occurrences"] = _(
                    "CNAB structure not recognized for this record."
                    " Report to system technical support."
                )
            event_value_dict["lot_id"] = return_lot_id.id
            event_value_dict["cnab_return_log_id"] = return_log_id.id
            return_event_obj.create(event_value_dict)

    def _create_return_lots(self, batches, return_log_id):
        return_lot_obj = self.env["l10n_br_cnab.return.lot"]

        for batch in batches:
            lot_value_dict = {}
            lot_value_dict.update(
                self._get_dict_value_from_line(batch["header_batch_line"])
            )
            lot_value_dict.update(
                self._get_dict_value_from_line(batch["trailer_batch_line"])
            )
            return_lot_id = return_lot_obj.create(lot_value_dict)
            self._create_return_events(batch["details"], return_lot_id, return_log_id)

    def _calculate_totals(self, return_log_id):
        # Set number of events
        return_log_id.number_events = len(return_log_id.event_ids)

        # Set number of lots
        lots = return_log_id.event_ids.mapped("lot_id")
        unic_lots = list(dict.fromkeys(lots))
        return_log_id.number_lots = len(unic_lots)

        liq_event_ids = return_log_id.event_ids.filtered(
            lambda e: e.gen_liquidation_move
        )
        if liq_event_ids:
            return_log_id.amount_total_title = sum(liq_event_ids.mapped("title_value"))
            return_log_id.amount_total_received = sum(
                liq_event_ids.mapped("payment_value")
            )
            return_log_id.amount_total_tariff_charge = sum(
                liq_event_ids.mapped("tariff_charge")
            )
            return_log_id.amount_total_interest_fee = sum(
                liq_event_ids.mapped("interest_fee_value")
            )
            return_log_id.amount_total_discount = sum(
                liq_event_ids.mapped("discount_value")
            )
            return_log_id.amount_total_rebate = sum(
                liq_event_ids.mapped("rebate_value")
            )

    def _check_company(self, return_dict):
        cnpj_cpf = "".join(char for char in self.company_id.cnpj_cpf if char.isdigit())
        if cnpj_cpf.zfill(14) != str(return_dict["cnpj_cpf"]).zfill(14):
            raise UserError(
                _("CNPJ/CPF of your active company is different of the file.")
            )
        if self.company_id != self.journal_id.company_id:
            raise UserError(_("Selected company is different of the Journal company."))

    def _check_duplicity(self, header_file):
        return_log_obj = self.env["l10n_br_cnab.return.log"]
        return_log_id = return_log_obj.search([("header_file", "=", header_file)])
        if return_log_id:
            raise UserError(_("This CNAB file has already imported."))

    def _create_return_log(self, data):
        self._check_duplicity(data["header_file_line"]["raw_line"])
        return_log_obj = self.env["l10n_br_cnab.return.log"]
        return_dict = {
            "name": f"Banco {self.journal_id.bank_id.short_name}  - "
            f"Conta {self.journal_id.bank_account_id.acc_number}",
            "filename": self.filename,
            "cnab_date_import": fields.Datetime.now(),
            "journal_id": self.journal_id.id,
            "return_file": self.return_file,
            "cnab_structure_id": self.cnab_structure_id.id,
            "company_id": self.company_id.id,
            "state": "draft",
            "header_file": data["header_file_line"]["raw_line"],
        }
        return_dict.update(self._get_dict_value_from_line(data["header_file_line"]))
        return_dict.update(self._get_dict_value_from_line(data["trailer_file_line"]))
        self._check_company(return_dict)
        return_log_id = return_log_obj.create(return_dict)

        self._create_return_lots(data["batches"], return_log_id)

        self._calculate_totals(return_log_id)
        return return_log_id

    def _import_cnab_240(self):
        data = self._get_data_from_file()
        return_log_id = self._create_return_log(data)

        return return_log_id

    def import_cnab(self):
        if self.cnab_format == "240":
            return_log_id = self._import_cnab_240()
        # TODO Implementar novos formatos CNABs
        else:
            raise UserError(_(f"CNAB Format {self.cnab_format} not implemented."))

        action = {
            "type": "ir.actions.act_window",
            "name": _("Export Data"),
            "res_model": "l10n_br_cnab.return.log",
            "res_id": return_log_id.id,
            "view_mode": "form",
            "view_id": self.env.ref(
                "l10n_br_cnab_structure.l10n_br_cnab_return_log_form_view_structure"
            ).id,
            "target": "current",
        }

        return action
