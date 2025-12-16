# Copyright (C) 2024 Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_CTE


class DocumentImporterWizardMixin(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    @api.model
    def _detect_binding(self, binding):
        """
        Register the CTe importer
        """
        if hasattr(binding, "infCte") or hasattr(binding, "CTe"):
            return self._detect_document_type(MODELO_FISCAL_CTE)
        return super()._detect_binding(binding)

    def _extract_binding_data(self, binding):
        res = super()._extract_binding_data(binding)
        if hasattr(binding, "CTe"):
            binding = binding.CTe
        if self.document_type == MODELO_FISCAL_CTE:
            self._extract_key_information(binding.infCte.Id[3:])
        return res

    def _destination_partner_from_binding(self, binding):
        if self.document_type == MODELO_FISCAL_CTE:
            self.destination_partner_id = self._search_partner(
                cnpj=binding.infCte.dest.CNPJ,
                legal_name=binding.infCte.dest.xNome,
            )
            self.issuer_legal_name = binding.infCte.emit.xNome
            self.issuer_name = binding.infCte.emit.xFant

            self.destination_cnpj = formata(binding.infCte.dest.CNPJ)
            self.destination_name = binding.infCte.dest.xNome

    def _create_edoc_from_file(self):
        if self.document_type == MODELO_FISCAL_CTE:
            binding = self._parse_file()
            edoc = self.env["l10n_br_fiscal.document"].import_binding_cte(
                binding,
                edoc_type=self.fiscal_operation_type,
            )
            edoc.document_type_id = self.env.ref("l10n_br_fiscal.document_57").id
            edoc.fiscal_operation_id = self.fiscal_operation_id
            return binding, edoc
        return super()._create_edoc_from_file()
