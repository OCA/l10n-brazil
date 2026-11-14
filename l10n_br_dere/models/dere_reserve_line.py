# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DereReserveLine(models.Model):
    _name = "l10n_br_dere.reserve.line"
    _description = "DeRE technical-reserve investment line"
    _inherit = "dere.12.detativo"
    _order = "dere12_cCta, dere12_idAtivo"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="declaration_id.company_id", store=True, index=True
    )
    asset_id = fields.Many2one(
        comodel_name="l10n_br_dere.reserve.asset",
        string="Reserve asset",
        ondelete="restrict",
    )
    pgcc_account_id = fields.Many2one(
        comodel_name="l10n_br_dere.pgcc.account",
        string="PGCC account",
        ondelete="restrict",
    )
    dere12_cCta = fields.Char(
        string="Account",
        required=True,
        size=53,
        help="Official DeRE field cCta.",
    )
    dere12_idAtivo = fields.Char(
        string="Asset id",
        required=True,
        size=30,
        help="Official DeRE field idAtivo.",
    )
    dere12_descAtivo = fields.Char(
        string="Asset description",
        required=True,
        size=255,
        help="Official DeRE field descAtivo.",
    )
    dere12_vSaldoInic = fields.Monetary(
        string="Opening balance",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vSaldoInic.",
    )
    dere12_vRendPerReceb = fields.Monetary(
        string="Period income received",
        currency_field="brl_currency_id",
        help="Official DeRE field vRendPerReceb.",
    )
    dere12_vVarMensal = fields.Monetary(
        string="Monthly variation",
        currency_field="brl_currency_id",
        help="Official DeRE field vVarMensal.",
    )
    dere12_vPrincLiqResg = fields.Monetary(
        string="Principal redeemed",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vPrincLiqResg.",
    )
    dere12_vRendLiqResg = fields.Monetary(
        string="Income on redemption",
        currency_field="brl_currency_id",
        help="Official DeRE field vRendLiqResg.",
    )
    dere12_vSaldoFinal = fields.Monetary(
        string="Closing balance",
        currency_field="brl_currency_id",
        compute="_compute_amounts",
        store=True,
        help="Official DeRE field vSaldoFinal.",
    )
    dere12_vApur = fields.Monetary(
        string="Taxable amount",
        currency_field="brl_currency_id",
        compute="_compute_amounts",
        store=True,
        help="Official DeRE field vApur.",
    )

    @api.depends(
        "dere12_vSaldoInic",
        "dere12_vVarMensal",
        "dere12_vPrincLiqResg",
        "dere12_vRendPerReceb",
        "dere12_vRendLiqResg",
    )
    def _compute_amounts(self):
        for rec in self:
            rec.dere12_vSaldoFinal = (
                rec.dere12_vSaldoInic + rec.dere12_vVarMensal - rec.dere12_vPrincLiqResg
            )
            rec.dere12_vApur = rec.dere12_vRendPerReceb + rec.dere12_vRendLiqResg

    @api.constrains("dere12_vSaldoFinal", "dere12_vApur")
    def _check_positive_totals(self):
        for rec in self:
            if rec.dere12_vSaldoFinal < -0.005:
                raise ValidationError(
                    _("The D-1106 closing balance cannot be negative for asset %s.")
                    % rec.dere12_idAtivo
                )
            if rec.dere12_vApur < -0.005:
                raise ValidationError(
                    _("The D-1106 taxable amount cannot be negative for asset %s.")
                    % rec.dere12_idAtivo
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
            "idAtivo": self.dere12_idAtivo,
            "descAtivo": self.dere12_descAtivo,
            "vSaldoInic": self.dere12_vSaldoInic,
            "vRendPerReceb": self.dere12_vRendPerReceb,
            "vVarMensal": self.dere12_vVarMensal,
            "vPrincLiqResg": self.dere12_vPrincLiqResg,
            "vRendLiqResg": self.dere12_vRendLiqResg,
            "vSaldoFinal": self.dere12_vSaldoFinal,
            "vApur": self.dere12_vApur,
        }
