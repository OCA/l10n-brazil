# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN, FISCAL_OUT
from odoo.addons.l10n_br_fiscal_dfe.tools import utils
from odoo.addons.l10n_br_fiscal_edi.models.document_import import (
    LAST_PARTNER_CONTEXT_KEY,
)

from ..services.nfse_dfe_xml import decode_arquivo_xml, parse_nfse_file


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Service Product",
        domain="[('type', '=', 'service')]",
    )

    def _parse_file(self):
        binding = parse_nfse_file(self.file)
        if binding:
            return binding
        return super()._parse_file()

    def _detect_binding(self, binding):
        if getattr(binding, "is_national_nfse", False):
            self._detect_document_type("SE")
            return
        return super()._detect_binding(binding)

    def _extract_binding_data(self, binding):
        if not getattr(binding, "is_national_nfse", False):
            return super()._extract_binding_data(binding)
        provider = binding.provider or {}
        provider_digits = (
            provider.get("cnpj") or provider.get("cpf") or binding.provider_cnpj
        )
        self.document_key = binding.access_key
        self.document_number = (binding.number or "").lstrip("0") or binding.number
        self.document_serie = binding.serie
        self.issuer_legal_name = provider.get("legal_name") or binding.provider_name
        self.issuer_cnpj = formata(provider_digits) if provider_digits else False
        self.issuer_partner_id = (
            self._search_partner(cnpj=provider_digits) if provider_digits else False
        )
        self.partner_id = self.issuer_partner_id
        if not self.product_id and self.company_id.nfse_import_product_id:
            self.product_id = self.company_id.nfse_import_product_id
        self.issuer_type_in_out = FISCAL_OUT
        self.rps_number = binding.rps_number
        company_digits = re.sub(r"\D", "", self.company_id.vat or "")
        self.destination_cnpj = (
            utils.mask_cnpj(company_digits) if company_digits else False
        )
        self.destination_partner_id = self.company_id.partner_id
        self.destination_type_in_out = FISCAL_IN
        self.fiscal_operation_id = self.env[
            "l10n_br_fiscal.document"
        ]._nfse_default_operation()

    def _create_edoc_from_file(self):
        binding = self._parse_file()
        if not getattr(binding, "is_national_nfse", False):
            return super()._create_edoc_from_file()
        documents = self.env["l10n_br_fiscal.document"].with_company(self.company_id)
        parsed = documents._nfse_parsed_file(
            binding, f"NFSe-{binding.access_key}.xml", decode_arquivo_xml(self.file)
        )
        last_partner = self.env["res.partner"].search([], order="id desc", limit=1)
        document = documents._nfse_import_create(
            binding,
            partner=self.partner_id or self.issuer_partner_id,
            product=self.product_id,
            operation=self.fiscal_operation_id,
        )
        document.with_context(
            **{LAST_PARTNER_CONTEXT_KEY: last_partner.id}
        )._edi_import_after_create(parsed, "taker")
        if not self.partner_id:
            self.partner_id = document.partner_id
        self.document_id = document
        return binding, document
