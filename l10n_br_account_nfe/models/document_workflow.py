# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EDOC_PURPOSE_AJUSTE,
    EDOC_PURPOSE_DEVOLUCAO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
)


def filter_nfe(record):
    if (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code
        in [
            MODELO_FISCAL_NFE,
            MODELO_FISCAL_NFCE,
        ]
        and record.issuer == DOCUMENT_ISSUER_COMPANY
    ):
        return True
    return False


class DocumentWorkflow(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.workflow"

    def action_document_confirm(self):
        for record in self.filtered(filter_nfe):
            record.nfe40_dup = [(5,)]
            record.nfe40_detPag = [(5,)]
            ind_pag = "0"
            fiscal_payment_mode = "90"
            v_pag = 0.00
            if record.amount_financial_total and record.edoc_purpose not in (
                EDOC_PURPOSE_DEVOLUCAO,
                EDOC_PURPOSE_AJUSTE,
            ):
                # TAG - Cobrança
                duplicatas = record.env["nfe.40.dup"]
                count = 1
                for mov in record.move_ids.financial_move_line_ids:
                    duplicatas += duplicatas.create(
                        {
                            "nfe40_nDup": str(count).zfill(3),
                            "nfe40_dVenc": mov.date_maturity,
                            "nfe40_vDup": mov.debit,
                        }
                    )
                    count += 1
                record.nfe40_dup = [(6, 0, duplicatas.ids)]

                # TAG - Pagamento
                if (
                    record.move_ids.payment_mode_id
                    and not record.move_ids.payment_mode_id.fiscal_payment_mode
                ):
                    raise UserError(
                        _(
                            "Payment Mode {} should has Fiscal Payment Mode"
                            " filled to be used in Fiscal Document!"
                        ).format(record.move_ids.payment_mode_id.name)
                    )

                moves_terms = record.move_ids.financial_move_line_ids.filtered(
                    lambda move_line: move_line.date_maturity > move_line.date
                )
                ind_pag = "1" if len(moves_terms) > 0 else "0"
                fiscal_payment_mode = (
                    record.move_ids.payment_mode_id.fiscal_payment_mode
                )
                v_pag = record.amount_financial_total

            pagamentos = record.env["nfe.40.detpag"].create(
                {
                    "nfe40_indPag": ind_pag,
                    "nfe40_tPag": fiscal_payment_mode,
                    "nfe40_vPag": v_pag,
                }
            )

            record.nfe40_detPag = [(6, 0, pagamentos.ids)]

        return super().action_document_confirm()
