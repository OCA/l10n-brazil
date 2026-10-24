# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import NAT_SALDO


class DereTrialLine(models.Model):
    _name = "l10n_br_dere.trial.line"
    _description = "DeRE trial-balance line"
    _inherit = "dere.12.balanceteconta"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="declaration_id.company_id", store=True, index=True
    )
    pgcc_account_id = fields.Many2one(
        comodel_name="l10n_br_dere.pgcc.account",
        string="PGCC account",
        required=True,
        ondelete="restrict",
    )
    dere12_cCta = fields.Char(
        related="pgcc_account_id.dere12_cCta",
        store=True,
        string="Account",
        help="Official DeRE field cCta.",
    )
    account_name = fields.Char(
        related="pgcc_account_id.account_id.name",
        string="Account name",
        help="Accounting account name, translated for the current user.",
    )
    dere12_natSaldoInic = fields.Selection(
        NAT_SALDO,
        string="Opening nature",
        required=True,
        help="Official DeRE field natSaldoInic.",
    )
    dere12_vSaldoInic = fields.Monetary(
        string="Opening balance",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vSaldoInic.",
    )
    dere12_vMovDebt = fields.Monetary(
        string="Debit",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vMovDebt.",
    )
    dere12_vAjusteDebt = fields.Monetary(
        string="Debit adjustment",
        currency_field="brl_currency_id",
        help="Official DeRE field vAjusteDebt.",
    )
    dere12_vMovCred = fields.Monetary(
        string="Credit",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vMovCred.",
    )
    dere12_vAjusteCred = fields.Monetary(
        string="Credit adjustment",
        currency_field="brl_currency_id",
        help="Official DeRE field vAjusteCred.",
    )
    dere12_natSaldoFinal = fields.Selection(
        NAT_SALDO,
        string="Closing nature",
        required=True,
        help="Official DeRE field natSaldoFinal.",
    )
    dere12_vSaldoFinal = fields.Monetary(
        string="Closing balance",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vSaldoFinal.",
    )
    dere12_natVApur = fields.Selection(
        NAT_SALDO,
        string="Taxable nature",
        help="Official DeRE field natVApur.",
    )
    dere12_vApur = fields.Monetary(
        string="Taxable amount",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vApur.",
    )

    def write(self, vals):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().unlink()

    def _to_xml_vals(self):
        self.ensure_one()
        return {
            "cCta": self.dere12_cCta,
            "natSaldoInic": self.dere12_natSaldoInic,
            "vSaldoInic": self.dere12_vSaldoInic,
            "vMovDebt": self.dere12_vMovDebt,
            "vAjusteDebt": self.dere12_vAjusteDebt,
            "vMovCred": self.dere12_vMovCred,
            "vAjusteCred": self.dere12_vAjusteCred,
            "natSaldoFinal": self.dere12_natSaldoFinal,
            "vSaldoFinal": self.dere12_vSaldoFinal,
            "natVApur": self.dere12_natVApur,
            "vApur": self.dere12_vApur,
        }
