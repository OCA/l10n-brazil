# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.osv import expression


class DataAbstract(models.AbstractModel):
    _name = "l10n_br_hr.data.abstract"
    _description = "HR Data Abstract"
    _order = "code"

    code = fields.Char(string="Code", required=True, index=True)

    name = fields.Text(string="Name", required=True, index=True)

    @api.multi
    def name_get(self):
        return [(r.id, "{} - {}".format(r.code, r.name)) for r in self]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
        recs = self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
        return self.browse(recs).name_get()
