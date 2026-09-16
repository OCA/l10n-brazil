# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import NAT_SALDO


class DereTrialLine(models.Model):
    _name = "l10n_br_dere.trial.line"
    _description = "DeRE trial-balance line"

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
    c_cta = fields.Char(
        related="pgcc_account_id.c_cta",
        store=True,
        string="Account",
        help="Official DeRE field cCta.",
    )
    nat_saldo_inic = fields.Selection(
        NAT_SALDO,
        string="Opening nature",
        required=True,
        help="Official DeRE field natSaldoInic.",
    )
    v_saldo_inic = fields.Monetary(
        string="Opening balance",
        currency_field="currency_id",
        required=True,
        help="Official DeRE field vSaldoInic.",
    )
    v_mov_debt = fields.Monetary(
        string="Debit",
        currency_field="currency_id",
        required=True,
        help="Official DeRE field vMovDebt.",
    )
    v_ajuste_debt = fields.Monetary(
        string="Debit adjustment",
        currency_field="currency_id",
        help="Official DeRE field vAjusteDebt.",
    )
    v_mov_cred = fields.Monetary(
        string="Credit",
        currency_field="currency_id",
        required=True,
        help="Official DeRE field vMovCred.",
    )
    v_ajuste_cred = fields.Monetary(
        string="Credit adjustment",
        currency_field="currency_id",
        help="Official DeRE field vAjusteCred.",
    )
    nat_saldo_final = fields.Selection(
        NAT_SALDO,
        string="Closing nature",
        required=True,
        help="Official DeRE field natSaldoFinal.",
    )
    v_saldo_final = fields.Monetary(
        string="Closing balance",
        currency_field="currency_id",
        required=True,
        help="Official DeRE field vSaldoFinal.",
    )
    nat_v_apur = fields.Selection(
        NAT_SALDO,
        string="Taxable nature",
        help="Official DeRE field natVApur.",
    )
    v_apur = fields.Monetary(
        string="Taxable amount",
        currency_field="currency_id",
        required=True,
        help="Official DeRE field vApur.",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaration_id.company_id.currency_id",
        store=True,
        string="Currency",
    )

    def _to_xml_vals(self):
        self.ensure_one()
        return {
            "cCta": self.c_cta,
            "natSaldoInic": self.nat_saldo_inic,
            "vSaldoInic": self.v_saldo_inic,
            "vMovDebt": self.v_mov_debt,
            "vAjusteDebt": self.v_ajuste_debt,
            "vMovCred": self.v_mov_cred,
            "vAjusteCred": self.v_ajuste_cred,
            "natSaldoFinal": self.nat_saldo_final,
            "vSaldoFinal": self.v_saldo_final,
            "natVApur": self.nat_v_apur,
            "vApur": self.v_apur,
        }
