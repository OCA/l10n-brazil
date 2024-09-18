# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EDOC_PURPOSE_AJUSTE,
    EDOC_PURPOSE_DEVOLUCAO,
)

A_PRAZO = "1"
A_VISTA = "0"
SEM_PAGAMENTO = "90"
NFE_IN = "0"
NFE_OUT = "1"


class DocumentNfe(models.Model):
    _inherit = "l10n_br_fiscal.document"

    ##########################
    # NF-e tag: Cob
    ##########################

    nfe40_dup = fields.One2many(
        comodel_name="nfe.40.dup",
        compute="_compute_nfe40_dup",
        store=True,
        copy=False,
        readonly=False,
    )

    ##########################
    # NF-e tag: dup
    # Compute Methods
    ##########################

    @api.depends("move_ids", "move_ids.financial_move_line_ids")
    def _compute_nfe40_dup(self):
        for record in self.filtered(lambda x: x._need_compute_nfe40_dup()):
            dups_vals = []
            for count, mov in enumerate(record.move_ids.financial_move_line_ids, 1):
                dups_vals.append(
                    {
                        "nfe40_nDup": str(count).zfill(3),
                        "nfe40_dVenc": mov.date_maturity,
                        "nfe40_vDup": mov.debit,
                    }
                )
            record.nfe40_dup = [(2, dup, 0) for dup in record.nfe40_dup.ids]
            record.nfe40_dup = [(0, 0, dup) for dup in dups_vals]

    ##########################
    # NF-e tag: Pag
    ##########################

    nfe40_detPag = fields.One2many(
        comodel_name="nfe.40.detpag",
        compute="_compute_nfe40_detpag",
        store=True,
        readonly=False,
    )

    ##########################
    # NF-e tag: detPag
    # Compute Methods
    ##########################

    @api.depends(
        "issuer",
        "move_ids",
        "move_ids.payment_mode_id",
        "move_ids.payment_mode_id.fiscal_payment_mode",
        "amount_financial_total",
        "nfe40_tpNF",
    )
    def _compute_nfe40_detpag(self):
        for rec in self.filtered(lambda x: x._need_compute_nfe_tags()):
            if rec._is_without_payment():
                det_pag_vals = {
                    "nfe40_indPag": A_VISTA,
                    "nfe40_tPag": SEM_PAGAMENTO,
                    "nfe40_vPag": 0.00,
                }
            else:
                # TODO pode haver pagamento que uma parte é a vista
                # e outra a prazo, dividir em dois detPag nestes casos.
                det_pag_vals = {
                    "nfe40_indPag": A_PRAZO if rec._is_installment() > 0 else A_VISTA,
                    "nfe40_tPag": rec.move_ids.payment_mode_id.fiscal_payment_mode
                    or "",
                    "nfe40_vPag": rec.amount_financial_total,
                }
            detpag_current = {
                field: getattr(detpag, field, None)
                for detpag in rec.nfe40_detPag
                for field in det_pag_vals
            }
            if det_pag_vals != detpag_current:
                rec.nfe40_detPag = [(2, detpag, 0) for detpag in rec.nfe40_detPag.ids]
                rec.nfe40_detPag = [(0, 0, det_pag_vals)]

    ################################
    # Business Model Methods
    ################################

    def _is_installment(self):
        """checks if the payment is in cash (á vista) or in installments (a prazo)"""
        self.ensure_one()
        self.move_ids.financial_move_line_ids.mapped("date_maturity")
        moves_terms = self.move_ids.financial_move_line_ids.filtered(
            lambda move_line: move_line.date_maturity > move_line.date
        )
        return True if len(moves_terms) > 0 else False

    def _need_compute_nfe40_dup(self):
        if (
            self._need_compute_nfe_tags()
            and self.amount_financial_total > 0
            and self.nfe40_tpNF == NFE_OUT
            and self.document_type != "65"
        ):
            return True
        else:
            return False

    def _is_without_payment(self):
        if self.edoc_purpose in (EDOC_PURPOSE_DEVOLUCAO, EDOC_PURPOSE_AJUSTE):
            return True
        if not self.amount_financial_total:
            return True
        if self.nfe40_tpNF == NFE_IN:
            return True
        else:
            return False

    @api.constrains("nfe40_detPag", "state_edoc")
    def _check_fiscal_payment_mode(self):
        for rec in self:
            if (
                rec.state_edoc == "em_digitacao"
                or not rec._need_compute_nfe_tags()
                or rec._is_without_payment()
            ):
                continue

            if not rec.move_ids.payment_mode_id:
                raise UserError(_("Payment Mode cannot be empty for this NF-e/NFC-e"))
            if not rec.move_ids.payment_mode_id.fiscal_payment_mode:
                raise UserError(
                    _(
                        "Payment Mode %(mode)s should have a Fiscal Payment Mode"
                        " filled to be used in the Fiscal Document!",
                        mode=rec.move_ids.payment_mode_id.name,
                    )
                )

    def _update_nfce_for_offline_contingency(self):
        res = super()._update_nfce_for_offline_contingency()
        if self.move_ids:
            copy_invoice = self.move_ids[0].copy()
            copy_invoice.action_post()
        return res
