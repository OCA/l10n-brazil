# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    bank_id = fields.Many2one(comodel_name="res.bank", related="journal_id.bank_id")
    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method", compute="_compute_payment_method_ids"
    )
    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        domain="[('bank_id', '=', bank_id),('payment_method_id', 'in', payment_method_ids),('state', '=', 'approved')]",
    )

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        structure_obj = self.env["l10n_br_cnab.structure"]
        structure_ids = structure_obj.search(
            [
                ("bank_id", "=", self.bank_id.id),
                ("payment_method_id", "in", self.payment_method_ids.ids),
                ("state", "=", "approved"),
            ]
        )
        if len(structure_ids):
            self.cnab_structure_id = structure_ids[0]
        else:
            self.cnab_structure_id = [(5, 0, 0)]

    @api.depends("journal_id", "type")
    def _compute_payment_method_ids(self):
        for record in self:
            if record.type == "inbound":
                record.payment_method_ids = record.journal_id.inbound_payment_method_ids
            elif record.type == "outbound":
                record.payment_method_ids = (
                    record.journal_id.outbound_payment_method_ids
                )
            else:
                record.payment_method_ids = [(5, 0, 0)]

    def import_cnab(self):
        pass
