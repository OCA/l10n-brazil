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
    )
    l10n_br_dere_ind_cta = fields.Selection(IND_CTA, string="DeRE account indicator")
    l10n_br_dere_nat_cta = fields.Selection(NAT_CTA, string="DeRE account nature")
    l10n_br_dere_cod_nat = fields.Selection(COD_NAT, string="DeRE nature code")
    l10n_br_dere_cod_trib = fields.Many2one(
        comodel_name="l10n_br_dere.tax.code",
        string="DeRE taxation code",
    )
    l10n_br_dere_ind_trib_iss = fields.Selection(
        IND_TRIB_ISS, string="DeRE ISS indicator"
    )
    l10n_br_dere_cta_sup_id = fields.Many2one(
        comodel_name="account.account",
        string="DeRE parent account",
        ondelete="restrict",
    )
    l10n_br_dere_nivel_cta = fields.Integer(string="DeRE account level", default=1)
    l10n_br_dere_desc_cta = fields.Char(string="DeRE account description", size=600)

    @api.depends("l10n_br_dere_cta_interna", "l10n_br_dere_dbr_mista", "code")
    def _compute_l10n_br_dere_cta(self):
        for account in self:
            internal = account.l10n_br_dere_cta_interna or re.sub(
                r"[^0-9A-Za-z]", "", account.code or ""
            )
            split = account.l10n_br_dere_dbr_mista or "000"
            account.l10n_br_dere_cta = f"{internal}{split}" if internal else False

    @api.constrains("l10n_br_dere_dbr_mista")
    def _check_l10n_br_dere_dbr_mista(self):
        for account in self:
            split = account.l10n_br_dere_dbr_mista
            if split and not re.fullmatch(r"\d{3}", split):
                raise ValidationError(
                    _("The DeRE mixed-account split must use three digits (000-999).")
                )
