# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.osv import expression


class DataAbstract(models.AbstractModel):
    _name = "l10n_br_hr.data.abstract"
    _description = "HR Data Abstract"
    _order = "code"

    code = fields.Char(required=True, index=True)

    name = fields.Text(required=True, index=True)

    def name_get(self):
        return [(r.id, f"{r.code} - {r.name}") for r in self]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
            return self._search(
                expression.AND([domain, args]),
                limit=limit,
                access_rights_uid=name_get_uid,
            )
        return super()._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )
