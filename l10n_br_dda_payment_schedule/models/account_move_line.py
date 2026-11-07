# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    dda_debit_id = fields.Many2one(
        comodel_name="l10n_br_dda.debit",
        string="DDA Boleto",
        readonly=True,
        copy=False,
        index="btree_not_null",
        ondelete="set null",
    )
    dda_barcode_filled = fields.Boolean(
        string="Barcode from the DDA", readonly=True, copy=False
    )
    dda_barcode_divergent = fields.Boolean(
        string="Barcode Differs from the DDA",
        compute="_compute_dda_barcode_divergent",
    )

    @api.depends(
        "payment_barcode", "dda_debit_id.barcode", "dda_debit_id.digitable_line"
    )
    def _compute_dda_barcode_divergent(self):
        for line in self:
            code = line.dda_debit_id._dda_payment_barcode()
            line.dda_barcode_divergent = bool(
                code and line.payment_barcode and line.payment_barcode != code
            )
