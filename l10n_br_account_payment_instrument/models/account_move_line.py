# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    payment_instrument_id = fields.Many2one(comodel_name="l10n_br.payment.instrument")

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if (
            self.payment_instrument_id
            and self.payment_instrument_id.instrument_type == "boleto"
        ):
            vals["barcode"] = self.payment_instrument_id.boleto_barcode
        if (
            self.payment_instrument_id
            and self.payment_instrument_id.instrument_type == "pix_qrcode"
        ):
            vals["pix_qrcode_key"] = self.payment_instrument_id.pix_qrcode_key
            vals["pix_qrcode_txid"] = self.payment_instrument_id.pix_qrcode_txid
        return vals

    def open_payment_instruments(self):
        self.ensure_one()
        action = {
            "name": _("Payment Instrument"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "l10n_br.payment.instrument",
            "type": "ir.actions.act_window",
            "res_id": self.payment_instrument_id.id,
            "context": {"default_line_ids": [(6, 0, [self.id])]},
            "target": "new",
        }
        return action
