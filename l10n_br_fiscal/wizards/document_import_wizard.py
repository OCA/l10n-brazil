# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import logging

from erpbrasil.base.fiscal.cnpj_cpf import validar_cnpj, validar_cpf
from erpbrasil.base.fiscal.edoc import detectar_chave_edoc
from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (
    FISCAL_IN,
    FISCAL_IN_OUT,
    FISCAL_OUT,
)

_logger = logging.getLogger(__name__)

try:
    from xsdata.formats.dataclass.parsers import XmlParser
except ImportError:
    _logger.error(_("xsdata Python lib not installed!"))


class DocumentImportWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.import.wizard"
    _description = "Import Document Wizard"
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
        selection=FISCAL_IN_OUT,
        compute="_compute_fiscal_operation_type",
    )

    issuer_cnpj = fields.Char(string="Issuer CNPJ")
    issuer_legal_name = fields.Char()
    issuer_name = fields.Char(string="Fantasia")
    issuer_partner_id = fields.Many2one(
        comodel_name="res.partner",
    )
    issuer_type_in_out = fields.Selection(selection=FISCAL_IN_OUT, string="Issuer Type")

    destination_cnpj = fields.Char(string="Destination CNPJ")
    destination_name = fields.Char()
    destination_partner_id = fields.Many2one(
        comodel_name="res.partner",
    )
    destination_type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT, string="Destination Type"
    )

    @api.depends("issuer_cnpj", "company_id.cnpj_cpf")
    def _compute_fiscal_operation_type(self):
        if self.issuer_cnpj == self.company_id.cnpj_cpf:
            self.fiscal_operation_type = "out"
        else:
            self.fiscal_operation_type = "in"

    def _search_partner(self, cnpj=None, name=None, legal_name=None):
        """
        Search for a partner based on CNPJ, name, or legal name.

        This method searches for a partner in the `res.partner` model
        based on the provided CNPJ, name, or legal name.
        If a CNPJ is provided, it validates whether it is a
        company or an individual and constructs the search domain accordingly.

        If a legal name or name is provided, it constructs the
        search domain to match either the legal name or the name.
        If neither CNPJ nor legal name/name is provided, it raises a UserError.

        Args:
            cnpj (str, optional): The CNPJ or CPF of the partner.
            name (str, optional): The name of the partner.
            legal_name (str, optional): The legal name of the partner.

        Returns:
            recordset: A recordset of the found partner, limited to one result.

        Raises:
            UserError: If neither CNPJ nor legal name/name is provided.
        """
        if cnpj:
            if validar_cnpj(cnpj):
                domain = [("is_company", "=", True)]
            elif validar_cpf(cnpj):
                domain = [("is_company", "=", False)]
            domain.append(("cnpj_cpf_stripped", "=", punctuation_rm(cnpj)))
        elif legal_name or name:
            domain = [("is_company", "=", True)]
            domain.append(
                ["|", ("legal_name", "ilike", legal_name), ("name", "ilike", name)]
            )
        else:
            raise UserError(_("No CNPJ or Legal Name to search for a partner!"))
        return self.env["res.partner"].search(domain, limit=1)

    def _import_edoc(self):
        self._find_existing_document()
        if not self.document_id:
            binding, self.document_id = self._create_edoc_from_file()
        else:
            binding = self._parse_file()
        return binding, self.document_id

    def action_import_and_open_document(self):  # TODO used?
        self._import_edoc()
        return self.action_open_document()

    def _destination_partner_from_binding(self, binding):
        pass

    def _create_edoc_from_file(self):
        pass  # meant to be overriden

    def _detect_document_type(self, code):
        self.document_type_id = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", code)],
            limit=1,
        )

    def _find_existing_document(self):
        self.document_id = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", self.document_key.replace(" ", ""))],
            limit=1,
        )

    @api.onchange("file")
    def _onchange_file(self):
        if self.file:
            self._fill_wizard_from_binding()

    def _fill_wizard_from_binding(self):
        binding = self._parse_file()
        self._detect_binding(binding)
        self._extract_binding_data(binding)
        self._find_existing_document()
        self._destination_partner_from_binding(binding)
        return binding

    @api.model
    def _detect_binding(self, binding):
        """
        A pluggable method were each specialized fiscal document
        importation wizard can register itself and return a tuple
        with (the_fiscal_document_type_code, the_name_of_the_importation_wizard)
        """
        raise UserError(
            _("Importation not implemented for %s!")
            % (
                type(
                    binding,
                )
            )
        )

    def action_open_document(self):
        return {
            "name": _("Document Imported"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": self.document_id.id,
            "res_model": "l10n_br_fiscal.document",
        }

    def _extract_binding_data(self, binding):
        pass  # meant to be overriden

    def _extract_key_information(self, edoc_key):
        """TODO: Melhorar códifo da chave para não precisar
        remover o tipo de chave do prefixo:
            binding.NFe.infNFe.Id[3:]
        """
        edoc = detectar_chave_edoc(edoc_key)
        self.document_key = " ".join(edoc.partes())
        self.document_number = edoc.numero_documento.strip("0")
        self.document_serie = edoc.numero_serie.strip("0")
        self.issuer_cnpj = edoc.cnpj_cpf_emitente
        self.issuer_partner_id = self._search_partner(edoc.cnpj_cpf_emitente)
        if edoc.forma_emissao == "1":
            self.issuer_type_in_out = FISCAL_OUT
            self.destination_type_in_out = FISCAL_IN
        else:
            self.issuer_type_in_out = FISCAL_IN
            self.destination_type_in_out = FISCAL_OUT

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
        # NOTE: no try and a stacktrace does help for debug/support
        return XmlParser().from_bytes(base64.b64decode(file_data))
