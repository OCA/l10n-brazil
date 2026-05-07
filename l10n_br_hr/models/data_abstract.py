# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.fields import Domain


class DataAbstract(models.AbstractModel):
    _name = "l10n_br_hr.data.abstract"
    _description = "HR Data Abstract"
    _order = "code"

    code = fields.Char(required=True, index=True)

    name = fields.Text(required=True, index=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for r in self:
            r.display_name = f"{r.code} - {r.name}"

    @api.model
    def _search_display_name(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            return self._search(
                (Domain(domain) & Domain(args)).to_list(),
                limit=limit,
                access_rights_uid=name_get_uid,
            )
        return super()._search_display_name(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )
