# Copyright (C) 2024 Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_MDFE


class DocumentImporterWizardMixin(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    @api.model
    def _detect_binding(self, binding):
        """
        Register the import_xml MDFe importer
        """
        if hasattr(binding, "infMDFe"):
            return self._detect_document_type(MODELO_FISCAL_MDFE)
        return super()._detect_binding(binding)

    def _extract_binding_data(self, binding):
        res = super()._extract_binding_data(binding)
        if self.document_type == MODELO_FISCAL_MDFE:
            self._extract_key_information(binding.infMDFe.Id[3:])
        return res

    def _destination_partner_from_binding(self, binding):
        res = super()._document_key_from_binding(binding)
        if self.document_type == MODELO_FISCAL_MDFE:
            self.destination_partner_id = self._search_partner(
                cnpj=binding.infMDFe.dest.CNPJ,
                legal_name=binding.infMDFe.dest.xNome,
            )
            self.issuer_legal_name = binding.infMDFe.emit.xNome
            self.issuer_name = binding.infMDFe.emit.xFant

            self.destination_cnpj = formata(binding.infMDFe.dest.CNPJ)
            self.destination_name = binding.infMDFe.dest.xNome
        return res

    def _create_edoc_from_file(self):
        if self.document_type == MODELO_FISCAL_MDFE:
            binding = self._parse_file()
            edoc = self.env["l10n_br_fiscal.document"].import_binding_mdfe(
                binding,
                edoc_type=self.fiscal_operation_type,
            )
            return binding, edoc
        return super()._create_edoc_from_file()
