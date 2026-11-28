# License AGPL-3 - See [http://www.gnu.org/licenses/agpl-3.0.html](http://www.gnu.org/licenses/agpl-3.0.html)

from odoo import api, models
from odoo.fields import Command

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE
from odoo.addons.l10n_br_nfe.models.document import filter_processador_edoc_nfe


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends("move_ids.pos_order_ids.payment_ids.amount")
    def _compute_nfe40_detpag(self):
        res = super()._compute_nfe40_detpag()
        for rec in self.filtered(lambda d: d.document_type == MODELO_FISCAL_NFCE):
            rec._compute_nfe40_detpag_from_pos_payments()
        return res

    def _compute_nfe40_detpag_from_pos_payments(self):
        """A PoS order paid with more than one payment method gets one detPag
        per fiscal payment mode instead of a single one with the whole amount.
        The change stays in vTroco, so the amounts are the ones received."""
        self.ensure_one()
        payments = self.move_ids.pos_order_ids.payment_ids.filtered(
            lambda p: not p.is_change and p.amount > 0
        )
        amount_by_mode = {}
        for payment in payments:
            mode = payment.payment_method_id.payment_mode_id.fiscal_payment_mode
            if not mode:
                return
            amount_by_mode[mode] = amount_by_mode.get(mode, 0.0) + payment.amount
        if len(amount_by_mode) < 2:
            return
        current = {p.nfe40_tPag: p.nfe40_vPag for p in self.nfe40_detPag}
        if current == amount_by_mode and len(self.nfe40_detPag) == len(amount_by_mode):
            return
        ind_pag = self.nfe40_detPag[:1].nfe40_indPag
        self.nfe40_detPag = [Command.delete(p.id) for p in self.nfe40_detPag] + [
            Command.create(
                {"nfe40_indPag": ind_pag, "nfe40_tPag": mode, "nfe40_vPag": amount}
            )
            for mode, amount in amount_by_mode.items()
        ]

    def _serialize(self, edocs):
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            if record.document_type == MODELO_FISCAL_NFCE:
                record._document_qrcode()

        edocs = super()._serialize(edocs)

        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_nfe
        ):
            processor = record.processador_edoc

            record.flush_recordset()
            record.invalidate_recordset()

            if hasattr(record, "move_ids") and record.move_ids:
                record.move_ids.processador_edoc = processor

            record.processador_edoc = processor

        return edocs

    def _document_qrcode(self):
        res = super()._document_qrcode()

        for record in self.filtered(lambda d: d.document_type == MODELO_FISCAL_NFCE):
            if record.nfe40_infNFeSupl:
                record.nfe40_infNFeSupl.unlink()

            record.nfe40_infNFeSupl = self.env[
                "l10n_br_fiscal.document.supplement"
            ].create(
                {
                    "qrcode": record.get_nfce_qrcode(),
                    "url_key": record.get_nfce_qrcode_url(),
                }
            )

        return res
