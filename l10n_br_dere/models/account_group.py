# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import COD_NAT, NAT_CTA

# First digit of Brazilian CoA prefixes (ANS, XIPP, SPED-like).
_PREFIX_NAT_CTA = {
    "1": "D",
    "2": "C",
    "3": "C",
    "4": "D",
    "5": "D",
}
_PREFIX_COD_NAT = {
    "1": "1",
    "2": "2",
    "3": "4",
    "4": "5",
    "5": "5",
}


class AccountGroup(models.Model):
    _inherit = "account.group"

    l10n_br_dere_cta_interna = fields.Char(
        string="DeRE internal account",
        size=50,
        help="Alphanumeric internal code without dots or dashes. "
        "Defaults to the group prefix.",
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
    l10n_br_dere_nat_cta = fields.Selection(NAT_CTA, string="DeRE account nature")
    l10n_br_dere_cod_nat = fields.Selection(COD_NAT, string="DeRE nature code")
    l10n_br_dere_desc_cta = fields.Char(string="DeRE account description", size=600)
    l10n_br_dere_cta_sup = fields.Char(
        string="DeRE parent account",
        size=53,
        compute="_compute_l10n_br_dere_hierarchy",
    )
    l10n_br_dere_nivel_cta = fields.Integer(
        string="DeRE account level",
        compute="_compute_l10n_br_dere_hierarchy",
        recursive=True,
    )

    @api.depends(
        "l10n_br_dere_cta_interna",
        "l10n_br_dere_dbr_mista",
        "code_prefix_start",
    )
    def _compute_l10n_br_dere_cta(self):
        for group in self:
            internal = group._dere_internal_code()
            split = group.l10n_br_dere_dbr_mista or "000"
            group.l10n_br_dere_cta = f"{internal}{split}" if internal else False

    @api.depends(
        "parent_id",
        "parent_id.l10n_br_dere_cta",
        "parent_id.l10n_br_dere_nivel_cta",
    )
    def _compute_l10n_br_dere_hierarchy(self):
        for group in self:
            parent = group.parent_id
            group.l10n_br_dere_cta_sup = parent.l10n_br_dere_cta if parent else False
            group.l10n_br_dere_nivel_cta = (
                (parent.l10n_br_dere_nivel_cta or 0) + 1 if parent else 1
            )

    @api.constrains("l10n_br_dere_dbr_mista")
    def _check_l10n_br_dere_dbr_mista(self):
        for group in self:
            split = group.l10n_br_dere_dbr_mista
            if split and not re.fullmatch(r"\d{3}", split):
                raise ValidationError(
                    _("The DeRE mixed-account split must use three digits (000-999).")
                )

    def _dere_internal_code(self):
        self.ensure_one()
        return self.l10n_br_dere_cta_interna or re.sub(
            r"[^0-9A-Za-z]", "", self.code_prefix_start or ""
        )

    def _dere_cta_ref(self):
        """Return the stored referential code or the group prefix."""
        self.ensure_one()
        ref = self.l10n_br_dere_cta_ref or self._dere_internal_code()
        return ref[:13] if ref else False

    def _dere_nat_cta(self):
        self.ensure_one()
        if self.l10n_br_dere_nat_cta:
            return self.l10n_br_dere_nat_cta
        if self.parent_id:
            return self.parent_id._dere_nat_cta()
        prefix = self._dere_internal_code()
        return _PREFIX_NAT_CTA.get(prefix[0], "V") if prefix else False

    def _dere_cod_nat(self):
        self.ensure_one()
        if self.l10n_br_dere_cod_nat:
            return self.l10n_br_dere_cod_nat
        if self.parent_id:
            return self.parent_id._dere_cod_nat()
        prefix = self._dere_internal_code()
        return _PREFIX_COD_NAT.get(prefix[0]) if prefix else False

    def _dere_ancestors(self):
        groups = self.env["account.group"]
        current = self
        seen = set()
        while current and current.id not in seen:
            groups |= current
            seen.add(current.id)
            current = current.parent_id
        return groups
