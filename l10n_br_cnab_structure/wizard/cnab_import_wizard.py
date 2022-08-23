# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class CNABImportWizard(models.TransientModel):

    _name = "cnab.import.wizard"
    _description = "CNAB Import Wizard"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        help="Only journals where the CNAB Import is allowed.",
        required=True,
    )
    bank_account_cnab_id = fields.Many2one(
        comodel_name="account.account",
        related="journal_id.default_account_id",
        readonly=True,
    )
    return_file = fields.Binary("Return File")
    filename = fields.Char()
    type = fields.Selection(
        [
            ("inbound", "Inbound Payment"),
            ("outbound", "Outbound Payment"),
        ],
        string="Type",
    )

    def import_cnab(self):
        return False
