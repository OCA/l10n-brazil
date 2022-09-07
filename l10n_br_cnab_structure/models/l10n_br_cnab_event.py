# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class CNABReturnEvent(models.Model):

    _inherit = "l10n_br_cnab.return.event"

    bank_line_ref = fields.Char(
        string="Bank Line Reference",
        compute="_compute_bank_line_ref",
        inverse="_inverse_bank_line_ref",
    )

    def _compute_bank_line_ref(self):
        for rec in self:
            rec.bank_line_ref = rec.bank_payment_line_id.name

    def _inverse_bank_line_ref(self):
        for rec in self:
            rec.bank_payment_line_id = self.env["bank.payment.line"].search(
                [("name", "=", rec.bank_line_ref)]
            )
