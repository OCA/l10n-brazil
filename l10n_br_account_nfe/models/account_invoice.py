from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
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
            if record.amount_financial_total:
                # TAG - Cobrança
                duplicatas = record.env["nfe.40.dup"]
                count = 1
                for mov in record.invoice_ids.financial_move_line_ids:
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
                if not record.invoice_ids.payment_mode_id.fiscal_payment_mode:
                    raise UserError(
                        _(
                            "Payment Mode {} should has Fiscal Payment Mode"
                            " filled to be used in Fiscal Document!".format(
                                record.invoice_ids.payment_mode_id.name
                            )
                        )
                    )

                moves_terms = record.invoice_ids.financial_move_line_ids.filtered(
                    lambda move_line: move_line.date_maturity > move_line.date
                )
                ind_pag = "1" if len(moves_terms) > 0 else "0"
                fiscal_payment_mode = (
                    record.invoice_ids.payment_mode_id.fiscal_payment_mode
                )
                v_pag = record.amount_financial_total
            else:
                ind_pag = "0"
                fiscal_payment_mode = "90"
                v_pag = 0.00

            pagamentos = record.env["nfe.40.detpag"].create(
                {
                    "nfe40_indPag": ind_pag,
                    "nfe40_tPag": fiscal_payment_mode,
                    "nfe40_vPag": v_pag,
                }
            )

            record.nfe40_detPag = [(6, 0, pagamentos.ids)]

        super().action_document_confirm()
