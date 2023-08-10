# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE


class DocumentEletronic(models.AbstractModel):

    _inherit = "l10n_br_fiscal.document.workflow"

    def _generate_key(self):
        super()._generate_key()

        for record in self.filtered(
            lambda d: d.document_type_id.code == MODELO_FISCAL_NFCE
        ):
            date = fields.Datetime.context_timestamp(record, record.document_date)
            chave_edoc = ChaveEdoc(
                ano_mes=date.strftime("%y%m").zfill(4),
                cnpj_cpf_emitente=record.company_cnpj_cpf,
                codigo_uf=(
                    record.company_state_id and record.company_state_id.ibge_code or ""
                ),
                forma_emissao=int(self.nfe_transmission),
                modelo_documento=record.document_type_id.code or "",
                numero_documento=record.document_number or "",
                numero_serie=record.document_serie or "",
                validar=False,
            )
            record.document_key = chave_edoc.chave
