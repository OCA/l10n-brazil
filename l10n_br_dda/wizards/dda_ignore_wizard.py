# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import DEBIT_MODEL


class DdaIgnoreWizard(models.TransientModel):
    _name = "l10n_br_dda.ignore.wizard"
    _description = "Ignore DDA boletos"

    debit_ids = fields.Many2many(
        comodel_name=DEBIT_MODEL,
        relation="l10n_br_dda_ignore_wizard_debit_rel",
        column1="wizard_id",
        column2="debit_id",
        string="Boletos",
    )
    reason = fields.Char(required=True)

    def action_confirm(self):
        self.ensure_one()
        self.debit_ids.action_ignore(self.reason)
        return {"type": "ir.actions.act_window_close"}
