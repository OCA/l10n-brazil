# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_DRAFT
from odoo.addons.l10n_br_nfe.constants.nfe import SEM_PAGAMENTO


class DocumentNfe(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.constrains("nfe40_detPag", "state_edoc")
    def _check_fiscal_payment_mode(self):
        for rec in self:
            # the check runs when the document is confirmed, by who may have no
            # right on the invoices
            payment_mode = rec.sudo().move_ids.payment_mode_id
            if (
                rec.state_edoc == DOCUMENT_STATE_DRAFT
                or not rec._need_compute_nfe_tags()
                or rec._nfe_without_payment()
                or not payment_mode
                or payment_mode.fiscal_payment_mode == SEM_PAGAMENTO
            ):
                continue

            if not payment_mode.fiscal_payment_mode:
                raise UserError(
                    _(
                        "Payment Mode %(mode)s should have "
                        "a Fiscal Payment Mode filled to be used in "
                        "the Fiscal Document!",
                        mode=payment_mode.name,
                    )
                )

    def _update_nfce_for_offline_contingency(self):
        res = super()._update_nfce_for_offline_contingency()
        if self.move_ids:
            copy_invoice = self.move_ids[0].copy()
            copy_invoice.action_post()
        return res
