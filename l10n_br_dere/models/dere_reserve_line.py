# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DereReserveLine(models.Model):
    _name = "l10n_br_dere.reserve.line"
    _description = "DeRE technical-reserve investment line"
    _inherit = "spec.mixin.dere.currency"
    _order = "c_cta, id_ativo"

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
    id_ativo = fields.Char(
        string="Asset id",
        required=True,
        size=30,
        help="Official DeRE field idAtivo.",
    )
    desc_ativo = fields.Char(
        string="Asset description",
        required=True,
        size=255,
        help="Official DeRE field descAtivo.",
    )
    pgcc_account_id = fields.Many2one(
        comodel_name="l10n_br_dere.pgcc.account",
        string="PGCC account",
        ondelete="restrict",
    )
    c_cta = fields.Char(
        string="Account",
        required=True,
        size=53,
        help="Official DeRE field cCta.",
    )
    v_saldo_inic = fields.Monetary(
        string="Opening balance",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vSaldoInic.",
    )
    v_rend_per_receb = fields.Monetary(
        string="Period income received",
        currency_field="brl_currency_id",
        help="Official DeRE field vRendPerReceb.",
    )
    v_var_mensal = fields.Monetary(
        string="Monthly variation",
        currency_field="brl_currency_id",
        help="Official DeRE field vVarMensal.",
    )
    v_princ_liq_resg = fields.Monetary(
        string="Principal redeemed",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vPrincLiqResg.",
    )
    v_rend_liq_resg = fields.Monetary(
        string="Income on redemption",
        currency_field="brl_currency_id",
        help="Official DeRE field vRendLiqResg.",
    )
    v_saldo_final = fields.Monetary(
        string="Closing balance",
        currency_field="brl_currency_id",
        compute="_compute_amounts",
        store=True,
        help="Official DeRE field vSaldoFinal.",
    )
    v_apur = fields.Monetary(
        string="Taxable amount",
        currency_field="brl_currency_id",
        compute="_compute_amounts",
        store=True,
        help="Official DeRE field vApur.",
    )

    @api.depends(
        "v_saldo_inic",
        "v_var_mensal",
        "v_princ_liq_resg",
        "v_rend_per_receb",
        "v_rend_liq_resg",
    )
    def _compute_amounts(self):
        for rec in self:
            rec.v_saldo_final = (
                rec.v_saldo_inic + rec.v_var_mensal - rec.v_princ_liq_resg
            )
            rec.v_apur = rec.v_rend_per_receb + rec.v_rend_liq_resg

    @api.constrains("v_saldo_final", "v_apur")
    def _check_positive_totals(self):
        for rec in self:
            if rec.v_saldo_final < -0.005:
                raise ValidationError(
                    _("The D-1106 closing balance cannot be negative for asset %s.")
                    % rec.id_ativo
                )
            if rec.v_apur < -0.005:
                raise ValidationError(
                    _("The D-1106 taxable amount cannot be negative for asset %s.")
                    % rec.id_ativo
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
            "cCta": self.c_cta,
            "idAtivo": self.id_ativo,
            "descAtivo": self.desc_ativo,
            "vSaldoInic": self.v_saldo_inic,
            "vRendPerReceb": self.v_rend_per_receb,
            "vVarMensal": self.v_var_mensal,
            "vPrincLiqResg": self.v_princ_liq_resg,
            "vRendLiqResg": self.v_rend_liq_resg,
            "vSaldoFinal": self.v_saldo_final,
            "vApur": self.v_apur,
        }
