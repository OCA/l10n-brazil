# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_dda.constants import ACTIVE_STATES

HOLDING_STATES = ACTIVE_STATES + ("paid",)


class DdaDebit(models.Model):
    _inherit = "l10n_br_dda.debit"

    payment_schedule_warning = fields.Text(compute="_compute_payment_schedule_warning")

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            self._dda_sync_payment_instrument()
        return res

    def _dda_payment_barcode(self):
        """Barcode (44 digits) of the boleto, False if its check digits fail."""
        if not self:
            return False
        self.ensure_one()
        try:
            vals = self.env["account.move.line"]._normalize_payment_instrument_vals(
                {"payment_barcode": self.barcode or self.digitable_line}
            )
        except ValidationError:
            return False
        return vals["payment_barcode"]

    def _dda_sync_payment_instrument(self):
        """Set the boleto on the payable items it holds and take it off the
        others, with the barcode only where this module wrote it."""
        line_model = self.env["account.move.line"].sudo()
        current = line_model.search([("dda_debit_id", "in", self.ids)])
        for debit in self:
            lines = line_model
            if debit.state in HOLDING_STATES:
                lines = debit.allocation_ids.move_line_id.sudo()
            first = debit.allocation_ids.sorted("id")[:1].move_line_id
            code = debit._dda_payment_barcode()
            for line in current.filtered(lambda ln, d=debit: ln.dda_debit_id == d):
                if line in lines:
                    continue
                vals = {"dda_debit_id": False, "dda_barcode_filled": False}
                if line.dda_barcode_filled and line.payment_barcode == code:
                    vals["payment_barcode"] = False
                line.write(vals)
            for line in lines.filtered(lambda ln, d=debit: ln.dda_debit_id != d):
                vals = {"dda_debit_id": debit.id}
                if code and line == first and not line.payment_barcode:
                    vals.update(payment_barcode=code, dda_barcode_filled=True)
                line.write(vals)

    @api.depends(
        "amount",
        "state",
        "allocation_ids.move_line_id.payment_barcode",
        "allocation_ids.move_line_id.amount_residual",
    )
    def _compute_payment_schedule_warning(self):
        reader = self.env["l10n_br_payment_schedule.instrument.reader"]
        for debit in self:
            lines = debit.allocation_ids.move_line_id.filtered(
                lambda ln, d=debit: ln.dda_debit_id == d and not ln.reconciled
            )
            messages = []
            for line in lines.filtered("dda_barcode_divergent"):
                messages.append(
                    self.env._(
                        "The item %s already has another barcode, which was kept: "
                        "check which boleto to pay.",
                        line.display_name,
                    )
                )
            if len(debit.allocation_ids) == 1 and lines:
                messages.append(
                    reader.new({"move_line_id": lines.id})._get_amount_message(
                        debit.amount
                    )
                )
            debit.payment_schedule_warning = (
                "\n".join(message for message in messages if message) or False
            )
