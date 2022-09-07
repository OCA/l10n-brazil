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

    bank_id = fields.Many2one(
        comodel_name="res.bank",
    )

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
    )

    br_bank_code = fields.Char(
        string="Brazilian Bank Code",
        size=3,
        help="Brazilian Bank Code ex.: 001 is the code of Banco do Brasil",
        compute="_compute_br_bank_code",
        inverse="_inverse_br_bank_code",
    )

    type = fields.Selection(
        [
            ("inbound", "Inbound Payment"),
            ("outbound", "Outbound Payment"),
        ],
        string="Type",
    )

    def _compute_br_bank_code(self):
        for rec in self:
            rec.br_bank_code = rec.bank_id.code_bc

    def _inverse_br_bank_code(self):
        for rec in self:
            rec.bank_id = self.env["res.bank"].search(
                [("code_bc", "=", rec.br_bank_code)]
            )

    def testes(self):
        return False
