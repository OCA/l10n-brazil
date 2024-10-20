# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN_OUT_ALL

_logger = logging.getLogger(__name__)

try:
    from xsdata.formats.dataclass.parsers import XmlParser
except ImportError:
    _logger.error(_("xsdata Python lib not installed!"))


class DocumentImportWizardMixin(models.TransientModel):
    _name = "l10n_br_fiscal.document.import.wizard.mixin"
    _description = "Wizard Import Document Mixin"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company.id,
    )

    file = fields.Binary(string="File to Import")

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        domain="[('fiscal_operation_type', '=', fiscal_operation_type)]",
    )

    document_type = fields.Char()

    fiscal_operation_type = fields.Selection(
        string="Fiscal Operation Type", selection=FISCAL_IN_OUT_ALL
    )

    def _import_edoc(self):
        self._find_existing_document()
        if not self.document_id:
            binding, self.document_id = self._create_edoc_from_file()
        else:
            binding = self._parse_file()
        return binding, self.document_id

    def action_import_and_open_document(self):
        self._import_edoc()
        return self.action_open_document()

    def _create_edoc_from_file(self):
        pass  # meant to be overriden

    @api.onchange("file")
    def _onchange_file(self):
        if self.file:
            self._fill_wizard_from_binding()

    def _fill_wizard_from_binding(self):
        pass  # meant to be overriden

    def action_open_document(self):
        return {
            "name": _("Document Imported"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": self.document_id.id,
            "res_model": "l10n_br_fiscal.document",
        }

    def _document_key_from_binding(self, binding):
        pass  # meant to be overriden

    def _find_existing_document(self):
        document_key = self._document_key_from_binding(self._parse_file())
        self.document_id = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", document_key.chave)],
            limit=1,
        )

    def _find_document_type(self, code):
        return self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", code)],
            limit=1,
        )

    def _find_fiscal_operation(self, cfop, nat_op, fiscal_operation_type):
        """try to find a matching fiscal operation via an operation line"""
        operation_lines = self.env["l10n_br_fiscal.operation.line"].search(
            [
                ("state", "=", "approved"),
                ("fiscal_type", "=", fiscal_operation_type),
                ("cfop_external_id", "=", cfop),
            ],
        )
        for line in operation_lines:
            if line.fiscal_operation_id.name == nat_op:
                return line.fiscal_operation_id
        if operation_lines:
            return operation_lines[0].fiscal_operation_id

    def _parse_file(self):
        return self._parse_file_data(self.file)

    @api.model
    def _parse_file_data(self, file_data):
        try:
            binding = XmlParser().from_bytes(base64.b64decode(file_data))
        except Exception as e:
            raise UserError(_("Invalid file!")) from e
        return binding

    @api.model
    def _detect_binding(self, binding):
        """
        A pluggable method were each specialized fiscal document
        importation wizard can register itself and return a tuple
        with (the_fiscal_document_type_code, the_name_of_the_importation_wizard)
        """
        raise UserError(
            _(
                "Importation not implemented for %s!"
                % (
                    type(
                        binding,
                    )
                )
            )
        )
