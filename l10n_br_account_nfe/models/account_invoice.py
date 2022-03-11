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
        record.fiscal_document_id.processador_edoc == PROCESSADOR_OCA
        and record.fiscal_document_id.document_type_id.code
        in [
            MODELO_FISCAL_NFE,
            MODELO_FISCAL_NFCE,
        ]
        and record.fiscal_document_id.issuer == DOCUMENT_ISSUER_COMPANY
    ):
        return True
    return False


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def action_invoice_open(self):
        super(AccountInvoice, self).action_invoice_open()

        for inv in self.filtered(filter_nfe):
            if inv.amount_financial_total > 0:
                self.generate_payment_info(inv)
                self.generate_cobranca_info(inv)

    def generate_payment_info(self, inv):
        if not inv.payment_mode_id.fiscal_payment_mode:
            raise UserError(_("Document without Fiscal Payment Mode!"))

        moves_terms = inv.financial_move_line_ids.filtered(
            lambda move_line: move_line.date_maturity > move_line.date
        )
        indPag = "1" if len(moves_terms) > 0 else "0"

        inv.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                inv.fiscal_document_id._prepare_amount_financial(
                    indPag,
                    inv.payment_mode_id.fiscal_payment_mode,
                    inv.amount_financial_total,
                ),
            ),
        ]

    def generate_cobranca_info(self, inv):

        fat_id = self.env["nfe.40.fat"].create(
            {
                "nfe40_nFat": inv.number,
                "nfe40_vOrig": inv.amount_financial_total_gross,
                "nfe40_vDesc": inv.amount_financial_discount_value,
                "nfe40_vLiq": inv.amount_financial_total,
            }
        )

        duplicatas = self.env["nfe.40.dup"]
        count = 1
        for mov in inv.financial_move_line_ids:
            duplicatas += duplicatas.create(
                {
                    "nfe40_nDup": str(count).zfill(3),
                    "nfe40_dVenc": mov.date_maturity,
                    "nfe40_vDup": mov.debit,
                }
            )
            count += 1

        cobr_id = self.env["nfe.40.cobr"].create(
            {
                "nfe40_fat": fat_id.id,
                "nfe40_dup": [(6, 0, duplicatas.ids)],
            }
        )

        inv.update(
            {
                "nfe40_cobr": cobr_id.id,
            }
        )
