# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DereReserveAsset(models.Model):
    _name = "l10n_br_dere.reserve.asset"
    _description = "DeRE technical-reserve asset"
    _order = "id_ativo"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
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
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Accounting account",
        required=True,
        ondelete="restrict",
        domain="[('company_ids', 'in', company_id), "
        "('l10n_br_dere_reserve_invest', '=', True)]",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "id_ativo_company_uniq",
            "unique(id_ativo, company_id)",
            "The technical-reserve asset id must be unique per company.",
        )
    ]

    @api.depends("id_ativo", "desc_ativo")
    def _compute_name(self):
        for rec in self:
            rec.name = " ".join(filter(None, [rec.id_ativo, rec.desc_ativo]))

    @api.constrains("id_ativo")
    def _check_id_ativo(self):
        for rec in self:
            if rec.id_ativo and not re.fullmatch(r"[0-9A-Za-z]{1,30}", rec.id_ativo):
                raise ValidationError(
                    _("The DeRE asset id must be 1 to 30 alphanumeric characters.")
                )
