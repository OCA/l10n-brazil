# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    COD_NAT,
    IND_CTA,
    IND_TRIB_ISS,
    NAT_CTA,
)


class AccountAccount(models.Model):
    _inherit = "account.account"

    l10n_br_dere_cta_interna = fields.Char(
        string="DeRE internal account",
        size=50,
        help="Alphanumeric internal code without dots or dashes.",
    )
    l10n_br_dere_dbr_mista = fields.Char(
        string="DeRE mixed-account split",
        size=3,
        default="000",
    )
    l10n_br_dere_cta = fields.Char(
        string="DeRE full account",
        size=53,
        compute="_compute_l10n_br_dere_cta",
        store=True,
    )
    l10n_br_dere_cta_ref = fields.Char(
        string="DeRE referential account",
        size=13,
        help="Leave empty to inherit the referential code from the account group.",
    )
    l10n_br_dere_ind_cta = fields.Selection(
        IND_CTA,
        string="DeRE account indicator",
        compute="_compute_l10n_br_dere_hierarchy",
        help="Analytic accounts are always A. Synthetic nodes live on account groups.",
    )
    l10n_br_dere_nat_cta = fields.Selection(
        NAT_CTA,
        string="DeRE account nature",
        help="Leave empty to inherit the nature from the account group.",
    )
    l10n_br_dere_cod_nat = fields.Selection(
        COD_NAT,
        string="DeRE nature code",
        help="Leave empty to inherit the nature code from the account group.",
    )
    l10n_br_dere_cod_trib = fields.Many2one(
        comodel_name="l10n_br_dere.tax.code",
        string="DeRE taxation code",
    )
    l10n_br_dere_cod_trib_description = fields.Text(
        related="l10n_br_dere_cod_trib.description",
        string="Taxation code description",
    )
    l10n_br_dere_ind_trib_iss = fields.Selection(
        IND_TRIB_ISS, string="DeRE ISS indicator"
    )
    l10n_br_dere_cta_sup_id = fields.Many2one(
        comodel_name="account.group",
        string="DeRE parent group",
        ondelete="restrict",
        help="Leave empty to use the prefix account group. Set only when the "
        "chart is not prefix-based.",
    )
    l10n_br_dere_nivel_cta = fields.Integer(
        string="DeRE account level",
        compute="_compute_l10n_br_dere_hierarchy",
    )
    l10n_br_dere_desc_cta = fields.Char(string="DeRE account description", size=600)
    l10n_br_dere_reserve_invest = fields.Boolean(
        string="DeRE technical-reserve investment",
        help="Mark analytic accounts that hold technical-reserve investments "
        "reported on D-1106.",
    )
    l10n_br_dere_reserve_income_account_id = fields.Many2one(
        comodel_name="account.account",
        string="DeRE reserve income account",
        ondelete="restrict",
        help="Optional income account whose period credits fill D-1106 "
        "vRendPerReceb when the coupon does not hit the investment account.",
    )

    @api.depends("l10n_br_dere_cta_interna", "l10n_br_dere_dbr_mista", "code")
    def _compute_l10n_br_dere_cta(self):
        for account in self:
            internal = account._dere_internal_code()
            split = account.l10n_br_dere_dbr_mista or "000"
            account.l10n_br_dere_cta = f"{internal}{split}" if internal else False

    @api.depends(
        "l10n_br_dere_cta_ref",
        "l10n_br_dere_cta_sup_id",
        "l10n_br_dere_cta_sup_id.l10n_br_dere_nivel_cta",
        "group_id",
        "group_id.l10n_br_dere_cta_ref",
        "group_id.l10n_br_dere_nivel_cta",
    )
    def _compute_l10n_br_dere_hierarchy(self):
        for account in self:
            parent = account._dere_parent_group()
            account.l10n_br_dere_ind_cta = "A" if account._dere_cta_ref() else False
            account.l10n_br_dere_nivel_cta = (
                (parent.l10n_br_dere_nivel_cta or 0) + 1 if parent else 1
            )

    @api.constrains("l10n_br_dere_dbr_mista")
    def _check_l10n_br_dere_dbr_mista(self):
        for account in self:
            split = account.l10n_br_dere_dbr_mista
            if split and not re.fullmatch(r"\d{3}", split):
                raise ValidationError(
                    _("The DeRE mixed-account split must use three digits (000-999).")
                )

    def _dere_internal_code(self):
        self.ensure_one()
        return self.l10n_br_dere_cta_interna or re.sub(
            r"[^0-9A-Za-z]", "", self.code or ""
        )

    def _dere_parent_group(self):
        self.ensure_one()
        return self.l10n_br_dere_cta_sup_id or self.group_id

    def _dere_cta_ref(self):
        """Own mapping or an explicit group mapping. Prefix is not enough."""
        self.ensure_one()
        return self.l10n_br_dere_cta_ref or self.group_id.l10n_br_dere_cta_ref

    def _dere_nat_cta(self):
        self.ensure_one()
        if self.l10n_br_dere_nat_cta:
            return self.l10n_br_dere_nat_cta
        return self.group_id._dere_nat_cta() if self.group_id else False

    def _dere_cod_nat(self):
        self.ensure_one()
        if self.l10n_br_dere_cod_nat:
            return self.l10n_br_dere_cod_nat
        return self.group_id._dere_cod_nat() if self.group_id else False
