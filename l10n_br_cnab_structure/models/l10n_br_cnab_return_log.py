# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError


class L10nBrCNABReturnLog(models.Model):
    _inherit = "l10n_br_cnab.return.log"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
    )
    bank_account_cnab_id = fields.Many2one(
        comodel_name="account.account",
        related="journal_id.default_account_id",
        readonly=True,
    )
    return_file = fields.Binary()
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
    )
    header_file = fields.Char()
    cnpj_cpf = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    state = fields.Selection(selection=[("draft", "Draft"), ("confirmed", "Confirmed")])

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

    def action_confirm_return_log(self):
        self.ensure_one()
        for event in self.event_ids:
            event.confirm_event()
        self.state = "confirmed"

    def unlink(self):
        for return_log in self:
            if return_log.state == "confirmed":
                raise UserError(_("You cannot delete Return Log in confirmed state."))
        return super().unlink()
