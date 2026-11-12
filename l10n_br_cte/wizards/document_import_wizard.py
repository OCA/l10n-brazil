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
        if self.document_type != MODELO_FISCAL_CTE:
            return super()._destination_partner_from_binding(binding)
        # A cteProc (authorized XML, the one DF-e distributes) wraps the CTe
        if hasattr(binding, "CTe"):
            binding = binding.CTe
        infcte = binding.infCte
        self.issuer_legal_name = infcte.emit.xNome
        self.issuer_name = infcte.emit.xFant
        # dest is optional in the CT-e layout (e.g. toma3 without dest)
        dest = getattr(infcte, "dest", None)
        if dest is None:
            return None
        cnpj_cpf = dest.CNPJ or dest.CPF
        self.destination_partner_id = self._search_partner(
            cnpj=cnpj_cpf,
            legal_name=dest.xNome,
        )
        self.destination_cnpj = formata(cnpj_cpf) if cnpj_cpf else False
        self.destination_name = dest.xNome
        return None

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
