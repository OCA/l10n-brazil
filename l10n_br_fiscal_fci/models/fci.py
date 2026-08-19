# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    FCI_FIELD_SEPARATOR,
    FCI_FILE_ENCODING,
    FCI_FILE_LINE_SEPARATOR,
    FCI_LAYOUT_VERSION,
    FCI_MAX_LINES,
    FCI_STATE,
    FCI_TOTALIZED_REGISTERS,
    FCI_UTF8_STANDARD_TEXT,
)
from ..tools import sanitize_code, sanitize_text


class FCI(models.Model):
    """FCI file (Ficha de Conteúdo de Importação).

    Each record holds the data of one digital file to be transmitted to the
    tax administration through the SEFAZ Validador/Transmissor, following the
    layout of the Ato COTEPE ICMS 61/2012.
    """

    _name = "l10n_br_fiscal.fci.header"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "FCI"
    _order = "date desc, id desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        index=True,
    )

    date = fields.Datetime(
        string="Creation Date",
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        states={"draft": [("readonly", False)]},
        help="Date used to build the file name, as required by the layout.",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        states={"draft": [("readonly", False)]},
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency",
    )

    layout_version = fields.Char(
        required=True,
        readonly=True,
        default=FCI_LAYOUT_VERSION,
        help="Layout version of the file, register 0000 field VERSAO_LEIAUTE.",
    )

    state = fields.Selection(
        selection=FCI_STATE,
        string="Status",
        required=True,
        readonly=True,
        default="draft",
        tracking=True,
        copy=False,
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.fci.line",
        inverse_name="fci_id",
        string="Goods",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )

    line_count = fields.Integer(
        string="Goods Count",
        compute="_compute_line_count",
    )

    # Company data written in the registers 0000 and 0010.

    cnpj_cpf = fields.Char(
        related="company_id.cnpj_cpf",
        string="CNPJ",
    )

    legal_name = fields.Char(
        related="company_id.legal_name",
    )

    ie = fields.Char(
        related="company_id.l10n_br_ie_code",
        string="State Tax Number",
    )

    street_name = fields.Char(related="company_id.street_name")

    street_number = fields.Char(related="company_id.street_number")

    zip = fields.Char(related="company_id.zip")

    city_id = fields.Many2one(
        comodel_name="res.city",
        related="company_id.city_id",
        string="City",
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        related="company_id.state_id",
        string="State",
    )

    # Generated file.

    file = fields.Binary(
        string="FCI File",
        readonly=True,
        attachment=True,
        copy=False,
    )

    filename = fields.Char(
        string="File Name",
        readonly=True,
        copy=False,
    )

    # Data returned by the tax administration.

    protocol_number = fields.Char(
        string="Reception Protocol",
        readonly=True,
        states={"generated": [("readonly", False)]},
        copy=False,
        tracking=True,
        help="Protocol number returned by the TED after the transmission of "
        "the file. It is used to query the FCI control numbers on the web.",
    )

    hash_code = fields.Char(
        readonly=True,
        copy=False,
        help="Register 0000 field HASH_CODE of the return file.",
    )

    date_reception = fields.Char(
        string="Reception Date",
        readonly=True,
        copy=False,
        help="Register 0000 field DT_RECEPCAO_ARQUIVO of the return file.",
    )

    date_validation = fields.Char(
        string="Validation Date",
        readonly=True,
        copy=False,
        help="Register 0000 field DT_VALIDACAO_ARQUIVO of the return file.",
    )

    validation_indicator = fields.Char(
        readonly=True,
        copy=False,
        help="Register 0000 field IN_VALIDACAO_ARQUIVO of the return file.",
    )

    return_file = fields.Binary(
        readonly=True,
        attachment=True,
        copy=False,
    )

    return_filename = fields.Char(
        string="Return File Name",
        readonly=True,
        copy=False,
    )

    @api.depends("company_id", "date")
    def _compute_name(self):
        for record in self:
            cnpj = sanitize_code(record.company_id.cnpj_cpf) or "?"
            if record.date:
                date = fields.Datetime.context_timestamp(record, record.date)
                suffix = date.strftime("%Y%m%d-%H%M%S")
            else:
                suffix = "?"
            record.name = f"FCI/{cnpj}/{suffix}"

    @api.depends("line_ids")
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    def unlink(self):
        if self.filtered(lambda fci: fci.state != "draft"):
            raise UserError(_("You can only delete FCI in draft state!"))
        return super().unlink()

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault("date", fields.Datetime.now())
        return super().copy(default)

    ##########################################
    # FCI file generation
    ##########################################

    def _check_before_generate(self):
        """Run the pre-validations of the layout which we can check here."""
        self.ensure_one()
        errors = []
        if not self.line_ids:
            errors.append(_("The FCI must have at least one goods line."))
        if len(self.line_ids) > FCI_MAX_LINES:
            errors.append(
                _("A FCI file can not have more than %s goods lines.") % FCI_MAX_LINES
            )
        company = self.company_id
        if not sanitize_code(company.cnpj_cpf):
            errors.append(_("The company CNPJ is not filled in."))
        if not sanitize_code(company.l10n_br_ie_code):
            errors.append(_("The company State Tax Number is not filled in."))
        if not sanitize_code(company.zip):
            errors.append(_("The company ZIP code is not filled in."))
        if not company.city_id:
            errors.append(_("The company city is not filled in."))
        if not company.state_id:
            errors.append(_("The company state is not filled in."))
        for line in self.line_ids:
            errors += line._check_before_generate()
        if errors:
            raise UserError(
                _("The FCI %(name)s can not be generated:\n\n%(errors)s")
                % {"name": self.name, "errors": "\n".join("- %s" % e for e in errors)}
            )

    def _prepare_register(self, *fields_values):
        """Join the fields of a register with the pipe separator.

        The last field of a register must not be delimited, so no trailing
        separator is written.
        """
        return FCI_FIELD_SEPARATOR.join(str(value or "") for value in fields_values)

    def _prepare_register_0000(self):
        return self._prepare_register(
            "0000",
            sanitize_code(self.company_id.cnpj_cpf, 14),
            sanitize_text(self.company_id.name, 255),
            self.layout_version,
        )

    def _prepare_register_0001(self):
        return self._prepare_register("0001", FCI_UTF8_STANDARD_TEXT)

    def _prepare_register_0010(self):
        company = self.company_id
        address = " ".join(
            part for part in (company.street_name, company.street_number) if part
        )
        return self._prepare_register(
            "0010",
            sanitize_code(company.cnpj_cpf, 14),
            sanitize_text(company.legal_name or company.name, 255),
            sanitize_code(company.l10n_br_ie_code, 20),
            sanitize_text(address, 255),
            sanitize_code(company.zip, 8),
            sanitize_text(company.city_id.name, 255),
            company.state_id.code,
        )

    def _prepare_register_0990(self, block_lines):
        return self._prepare_register("0990", len(block_lines) + 1)

    def _prepare_register_5001(self):
        return self._prepare_register("5001")

    def _prepare_register_5990(self, block_lines):
        return self._prepare_register("5990", len(block_lines) + 1)

    def _prepare_register_9001(self):
        return self._prepare_register("9001")

    def _prepare_register_9900(self, registers):
        """Registers 9900: count of each totalized register type."""
        return [
            self._prepare_register("9900", register, count)
            for register, count in registers.items()
        ]

    def _prepare_register_9990(self, block_lines):
        # The register 9999 is not counted here, but the 9990 itself is.
        return self._prepare_register("9990", len(block_lines) + 1)

    def _prepare_register_9999(self, file_lines):
        # The register 9999 counts itself.
        return self._prepare_register("9999", len(file_lines) + 1)

    def _prepare_block_0(self):
        block = [
            self._prepare_register_0000(),
            self._prepare_register_0001(),
            self._prepare_register_0010(),
        ]
        block.append(self._prepare_register_0990(block))
        return block

    def _prepare_block_5(self):
        block = [self._prepare_register_5001()]
        block += [line._prepare_register_5020() for line in self.line_ids]
        block.append(self._prepare_register_5990(block))
        return block

    def _prepare_block_9(self, block_0, block_5):
        counters = {
            register: 0 for register in FCI_TOTALIZED_REGISTERS
        }  # keeps the layout order
        for file_line in block_0 + block_5:
            register = file_line.split(FCI_FIELD_SEPARATOR)[0]
            if register in counters:
                counters[register] += 1
        block = [self._prepare_register_9001()]
        block += self._prepare_register_9900(counters)
        block.append(self._prepare_register_9990(block))
        return block

    def _prepare_file_lines(self):
        self.ensure_one()
        block_0 = self._prepare_block_0()
        block_5 = self._prepare_block_5()
        block_9 = self._prepare_block_9(block_0, block_5)
        file_lines = block_0 + block_5 + block_9
        file_lines.append(self._prepare_register_9999(file_lines))
        return file_lines

    def _prepare_file_content(self):
        return FCI_FILE_LINE_SEPARATOR.join(self._prepare_file_lines())

    def _prepare_filename(self):
        """File name pattern of the layout: CNPJ_AAAAMMDD_hhmmss.txt"""
        self.ensure_one()
        date = fields.Datetime.context_timestamp(self, self.date)
        return "{}_{}.txt".format(
            sanitize_code(self.company_id.cnpj_cpf, 14),
            date.strftime("%Y%m%d_%H%M%S"),
        )

    def action_generate_file(self):
        for record in self:
            record._check_before_generate()
            content = record._prepare_file_content()
            record.write(
                {
                    "file": base64.b64encode(content.encode(FCI_FILE_ENCODING)),
                    "filename": record._prepare_filename(),
                    "state": "generated",
                }
            )
        return True

    def action_back_to_draft(self):
        for record in self:
            if record.state not in ("draft", "generated"):
                raise UserError(
                    _(
                        "The FCI %s was already transmitted and can not be "
                        "set back to draft."
                    )
                    % record.name
                )
            if record.line_ids.filtered("fci_code"):
                raise UserError(
                    _(
                        "The FCI %s already has FCI control numbers and can "
                        "not be set back to draft."
                    )
                    % record.name
                )
            record.write(
                {
                    "state": "draft",
                    "file": False,
                    "filename": False,
                }
            )
        return True

    def action_set_transmitted(self):
        for record in self:
            if not record.protocol_number:
                raise UserError(
                    _(
                        "Fill in the reception protocol returned by the "
                        "Validador/Transmissor before confirming the "
                        "transmission of the FCI %s."
                    )
                    % record.name
                )
            record.state = "transmitted"
        return True

    def action_import_return_file(self):
        """Open the wizard which reads the file returned by the SEFAZ."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_fiscal_fci.fci_import_wizard_action"
        )
        action["context"] = {"default_fci_id": self.id}
        return action
