# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DataAbstract(models.AbstractModel):
    _name = "l10n_br_hr.data.abstract"
    _description = "HR Data Abstract"
    _order = "code"
    _rec_names_search = ["code", "name"]

    code = fields.Char(required=True, index=True)

    name = fields.Text(required=True, index=True)

    def name_get(self):
        return [(r.id, f"{r.code} - {r.name}") for r in self]
