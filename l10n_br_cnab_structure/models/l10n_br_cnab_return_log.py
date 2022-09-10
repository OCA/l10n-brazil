# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class L10nBrCNABReturnLog(models.Model):

    _inherit = "l10n_br_cnab.return.log"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
    )
    bank_account_cnab_id = fields.Many2one(
        comodel_name="account.account",
        related="journal_id.default_account_id",
        readonly=True,
    )
    return_file = fields.Binary("Return File")
    bank_acc_number = fields.Char(
        compute="_compute_bank_acc_number",
        inverse="_inverse_bank_acc_number",
    )
    bank_id = fields.Many2one(comodel_name="res.bank", related="journal_id.bank_id")
    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
    )
    type = fields.Selection(
        [
            ("inbound", "Inbound Payment"),
            ("outbound", "Outbound Payment"),
        ],
        string="Type",
    )

    def _compute_bank_acc_number(self):
        for rec in self:
            rec.bank_acc_number = rec.bank_account_id.acc_number

    def _inverse_bank_acc_number(self):
        for rec in self:
            rec.bank_account_id = self.env["res.partner.bank"].search(
                [
                    ("acc_number", "=", rec.bank_acc_number),
                    ("bank_id", "=", rec.bank_id.id),
                ]
            )
