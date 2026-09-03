# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import io
import logging
import re
import zipfile
from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    FCI_FIELD_SEPARATOR,
    FCI_FILE_ENCODING,
    FCI_LAYOUT_VERSION,
)
from ..tools import sanitize_code, sanitize_text

_logger = logging.getLogger(__name__)

# File name pattern of the layout: CNPJ_AAAAMMDD_hhmmss.txt
FILENAME_PATTERN = re.compile(r"(\d{14})_(\d{8})_(\d{6})")


class FCIImportWizard(models.TransientModel):
    """Import a FCI digital file.

    Two kinds of file are accepted:

    - a transmission file, generated here or in another platform and not
      transmitted yet. A draft FCI is created from it, so that it can be
      reviewed and completed in Odoo;
    - a return file, downloaded from the restricted query of the FCI web
      system ("Download Arquivo de Retorno"). It has the same registers of
      the transmitted file plus the fields filled in by the system, among
      them the FCI control number of each goods (register 5020 field
      CODIGO_FCI). It updates the FCI it comes from, which is created when
      it is not in the database yet.

    The ZIP file downloaded from the FCI web system is accepted as well.
    """

    _name = "l10n_br_fiscal.fci.import.wizard"
    _description = "Import FCI File"

    fci_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.fci.header",
        string="FCI",
        ondelete="cascade",
        help="FCI updated by the return file. Leave it empty to create a new "
        "FCI from the imported file.",
    )

    file = fields.Binary(
        required=True,
        help="FCI file in the layout of the Ato COTEPE ICMS 61/2012, either "
        "a file to be transmitted or a file returned by the SEFAZ. The ZIP "
        "file downloaded from the FCI web system is also accepted.",
    )

    filename = fields.Char(string="File Name")

    result = fields.Text(readonly=True)

    state = fields.Selection(
        selection=[("init", "init"), ("done", "done")],
        readonly=True,
        default="init",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "l10n_br_fiscal.fci.header":
            values.setdefault("fci_id", self.env.context.get("active_id"))
        return values

    ##########################################
    # File parsing
    ##########################################

    def _get_file_content(self):
        """Return the decoded content of the file, unzipping it if needed."""
        self.ensure_one()
        content = base64.b64decode(self.file)
        if zipfile.is_zipfile(io.BytesIO(content)):
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                names = [
                    name
                    for name in zip_file.namelist()
                    if name.lower().endswith(".txt")
                ]
                if not names:
                    raise UserError(
                        _("No TXT file found inside the ZIP file %s.")
                        % (self.filename or "")
                    )
                content = zip_file.read(names[0])
        try:
            return content.decode(FCI_FILE_ENCODING)
        except UnicodeDecodeError as error:
            raise UserError(
                _(
                    "The file %s is not encoded in UTF-8, as required by the "
                    "FCI layout."
                )
                % (self.filename or "")
            ) from error

    def _parse_file(self, content):
        """Return the registers of the file as a dict of lists of fields."""
        registers = {}
        for file_line in content.splitlines():
            file_line = file_line.strip()
            if not file_line:
                continue
            values = file_line.split(FCI_FIELD_SEPARATOR)
            registers.setdefault(values[0], []).append(values)
        if "0000" not in registers or "5020" not in registers:
            raise UserError(
                _(
                    "The file %s does not look like a FCI file: the registers "
                    "0000 and 5020 were not found."
                )
                % (self.filename or "")
            )
        return registers

    @api.model
    def _get_field(self, register, index):
        """Return the value of a field of a register, empty when missing."""
        if len(register) > index:
            return register[index].strip()
        return ""

    def _is_return_file(self, registers):
        """A return file has the fields filled in by the system.

        In the transmission file the register 0000 stops at the layout
        version (4 fields).
        """
        return bool(self._get_field(registers["0000"][0], 6))

    ##########################################
    # Registers of the block 0
    ##########################################

    def _find_company(self, registers):
        cnpj = sanitize_code(self._get_field(registers["0000"][0], 1))
        companies = self.env["res.company"].search(
            [("id", "in", self.env.companies.ids)]
        )
        company = companies.filtered(lambda item: sanitize_code(item.cnpj_cpf) == cnpj)
        if not company:
            raise UserError(
                _(
                    "No allowed company found with the CNPJ %s of the file. "
                    "Check the CNPJ of your companies and the companies "
                    "enabled in your user."
                )
                % cnpj
            )
        return company[0]

    def _get_file_date(self, registers):
        """Date of the FCI, taken from the file name when it follows the
        pattern CNPJ_AAAAMMDD_hhmmss.txt of the layout."""
        match = FILENAME_PATTERN.search(self.filename or "")
        if match:
            try:
                date = datetime.strptime(
                    f"{match.group(2)}{match.group(3)}", "%Y%m%d%H%M%S"
                )
            except ValueError:
                _logger.warning("Invalid date in the file name %s", self.filename)
            else:
                # the file name holds the local time of the establishment
                timezone = pytz.timezone(self.env.user.tz or "UTC")
                return timezone.localize(date).astimezone(pytz.utc).replace(tzinfo=None)
        return fields.Datetime.now()

    def _prepare_header_values(self, registers):
        """Values of the registers 0000 and 0010 filled in by the system.

        0000|CNPJ|NAME|LAYOUT|HASH|DT_RECEPTION|COD_RECEPTION|DT_VALIDATION|
        IN_VALIDATION
        """
        register = registers["0000"][0]
        values = {}
        fields_map = {
            4: "hash_code",
            5: "date_reception",
            6: "protocol_number",
            7: "date_validation",
            8: "validation_indicator",
        }
        for index, field_name in fields_map.items():
            value = self._get_field(register, index)
            if value:
                values[field_name] = sanitize_text(value)
        return values

    ##########################################
    # Register 5020
    ##########################################

    def _find_product(self, register):
        """Find the product of a goods of the file.

        The goods are matched by their internal code (CODIGO_MERCADORIA) and,
        when no product has that code, by the GTIN (CODIGO_GTIN).
        """
        product_code = sanitize_text(self._get_field(register, 3))
        gtin = sanitize_code(self._get_field(register, 4))
        product = self.env["product.product"]
        if product_code:
            product = product.search([("default_code", "=", product_code)], limit=1)
        if not product and gtin:
            product = product.search([("barcode", "=", gtin)], limit=1)
        return product

    def _find_ncm(self, register):
        code = sanitize_code(self._get_field(register, 2))
        if not code:
            return self.env["l10n_br_fiscal.ncm"]
        return self.env["l10n_br_fiscal.ncm"].search(
            [("code_unmasked", "=", code)], limit=1
        )

    @api.model
    def _parse_amount(self, value):
        """Read an amount of the file, which uses the comma as decimal
        separator and no thousand separator."""
        if not value:
            return 0.0
        try:
            return float(value.replace(".", "").replace(",", "."))
        except ValueError as error:
            raise UserError(
                _("The amount %s of the file is not valid.") % value
            ) from error

    def _prepare_line_values(self, register):
        """Values of one goods of the file, register 5020."""
        product = self._find_product(register)
        ncm = self._find_ncm(register)
        return {
            "product_id": product.id,
            "name": sanitize_text(self._get_field(register, 1), 255),
            "ncm_id": ncm.id,
            "product_code": sanitize_text(self._get_field(register, 3), 50),
            "gtin": sanitize_code(self._get_field(register, 4), 14),
            "uom_code": sanitize_text(self._get_field(register, 5), 6),
            "amount_interstate": self._parse_amount(self._get_field(register, 6)),
            "amount_imported": self._parse_amount(self._get_field(register, 7)),
        }

    def _prepare_line_return_values(self, register):
        """Values of one goods filled in by the system, register 5020."""
        values = {}
        fci_code = self._get_field(register, 9)
        if fci_code:
            values["fci_code"] = sanitize_text(fci_code, 36)
        indicator = self._get_field(register, 10)
        if indicator:
            # The system returns the indicator followed by its description.
            values["validation_indicator"] = sanitize_code(indicator)[:3]
        return values

    ##########################################
    # Import
    ##########################################

    def _find_fci(self, registers):
        """Find the FCI a return file comes from.

        The file is matched by the hash code and by the reception protocol.
        Both are filled in by the tax administration, so a FCI transmitted
        from Odoo only has the protocol, typed in by the user.
        """
        fci_model = self.env["l10n_br_fiscal.fci.header"]
        header_values = self._prepare_header_values(registers)
        company_domain = [("company_id", "=", self._find_company(registers).id)]
        for field_name in ("hash_code", "protocol_number"):
            value = header_values.get(field_name)
            if not value:
                continue
            fci = fci_model.search(company_domain + [(field_name, "=", value)], limit=1)
            if fci:
                return fci
        return fci_model

    def _create_fci(self, registers, is_return):
        """Create a FCI from the registers of an imported file."""
        values = {
            "company_id": self._find_company(registers).id,
            "date": self._get_file_date(registers),
            "layout_version": self._get_field(registers["0000"][0], 3)
            or FCI_LAYOUT_VERSION,
            "line_ids": [
                (0, 0, self._prepare_line_values(register))
                for register in registers["5020"]
            ],
        }
        if is_return:
            values.update(self._prepare_header_values(registers))
            values.update(
                {
                    "state": "transmitted",
                    "return_file": self.file,
                    "return_filename": self.filename,
                }
            )
        else:
            values.update(
                {
                    "state": "draft",
                    "file": self.file,
                    "filename": self.filename,
                }
            )
        return self.env["l10n_br_fiscal.fci.header"].create(values)

    def _match_line(self, fci, register):
        """Find the line of the FCI matching a register 5020 of the file.

        The goods are matched by their internal code (CODIGO_MERCADORIA),
        which identifies the goods in the establishment, and by the NCM when
        the same code is used more than once.
        """
        product_code = sanitize_text(self._get_field(register, 3))
        ncm_code = sanitize_code(self._get_field(register, 2))
        lines = fci.line_ids.filtered(
            lambda line: sanitize_text(line.product_code) == product_code
        )
        if len(lines) > 1:
            lines = lines.filtered(lambda line: line.ncm_code == ncm_code)
        return lines[:1]

    def _import_return_values(self, fci, registers):
        """Write the FCI control numbers in the goods of the FCI."""
        imported = []
        rejected = []
        not_found = []
        for register in registers["5020"]:
            line = self._match_line(fci, register)
            if not line:
                not_found.append(sanitize_text(self._get_field(register, 3)))
                continue
            values = self._prepare_line_return_values(register)
            if values.get("fci_code"):
                imported.append(line.product_code)
            else:
                rejected.append(line.product_code)
            line.write(values)

        header_values = self._prepare_header_values(registers)
        header_values.update(
            {
                "return_file": self.file,
                "return_filename": self.filename,
            }
        )
        if imported:
            header_values["state"] = "done"
        fci.write(header_values)
        return imported, rejected, not_found

    def action_import(self):
        self.ensure_one()
        registers = self._parse_file(self._get_file_content())
        is_return = self._is_return_file(registers)
        fci = self.fci_id

        if fci:
            if not is_return:
                raise UserError(
                    _(
                        "The file %s is not a return file: it has no FCI "
                        "control number. Leave the FCI field empty to import "
                        "it as a new FCI."
                    )
                    % (self.filename or "")
                )
            if fci.state == "draft":
                raise UserError(
                    _(
                        "The FCI %s was not transmitted yet, there is no "
                        "return file to import."
                    )
                    % fci.name
                )
            self._check_company(fci, registers)
            result = self._prepare_return_result(
                fci, *self._import_return_values(fci, registers)
            )
        elif is_return:
            fci = self._find_fci(registers)
            if fci:
                result = self._prepare_return_result(
                    fci, *self._import_return_values(fci, registers)
                )
            else:
                fci = self._create_fci(registers, is_return)
                result = self._prepare_created_result(fci)
                result += "\n" + self._prepare_return_result(
                    fci, *self._import_return_values(fci, registers)
                )
        else:
            fci = self._create_fci(registers, is_return)
            result = self._prepare_created_result(fci)

        self.fci_id = fci
        self.result = result
        fci.message_post(body=result.replace("\n", "<br/>"))
        self.state = "done"
        return self._reopen()

    def _check_company(self, fci, registers):
        file_cnpj = sanitize_code(self._get_field(registers["0000"][0], 1))
        company_cnpj = sanitize_code(fci.company_id.cnpj_cpf)
        if file_cnpj and company_cnpj and file_cnpj != company_cnpj:
            raise UserError(
                _(
                    "The CNPJ %(file_cnpj)s of the file is different from the "
                    "CNPJ %(company_cnpj)s of the company of the FCI "
                    "%(name)s."
                )
                % {
                    "file_cnpj": file_cnpj,
                    "company_cnpj": company_cnpj,
                    "name": fci.name,
                }
            )

    ##########################################
    # Result of the import
    ##########################################

    def _prepare_created_result(self, fci):
        lines = [
            _("FCI %(name)s created with %(count)s goods.")
            % {"name": fci.name, "count": len(fci.line_ids)},
        ]
        without_product = fci.line_ids.filtered(lambda line: not line.product_id)
        if without_product:
            lines.append(
                _("%(count)s goods without a matching product: %(codes)s")
                % {
                    "count": len(without_product),
                    "codes": ", ".join(without_product.mapped("product_code")),
                }
            )
        without_ncm = fci.line_ids.filtered(lambda line: not line.ncm_id)
        if without_ncm:
            lines.append(
                _("%(count)s goods without a matching NCM: %(codes)s")
                % {
                    "count": len(without_ncm),
                    "codes": ", ".join(without_ncm.mapped("product_code")),
                }
            )
        return "\n".join(lines)

    def _prepare_return_result(self, fci, imported, rejected, not_found):
        lines = [
            _("Return file of the FCI %s imported.") % fci.name,
            _("%s FCI control number(s) imported.") % len(imported),
        ]
        if rejected:
            lines.append(
                _(
                    "%(count)s goods without FCI control number (rejected by "
                    "the tax administration): %(codes)s"
                )
                % {"count": len(rejected), "codes": ", ".join(rejected)}
            )
        if not_found:
            lines.append(
                _("%(count)s goods of the file not found in this FCI: %(codes)s")
                % {"count": len(not_found), "codes": ", ".join(not_found)}
            )
        return "\n".join(lines)

    ##########################################
    # Actions
    ##########################################

    @api.model
    def action_import_file(self, filename, file_data):
        """Import a file uploaded from the FCI list view."""
        wizard = self.create({"filename": filename, "file": file_data})
        return wizard.action_import()

    def action_open_fci(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.fci.header",
            "res_id": self.fci_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }

    def _reopen(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
        }
