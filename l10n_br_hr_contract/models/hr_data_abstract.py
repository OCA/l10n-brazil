# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrDataAbstract(models.AbstractModel):
    _name = "l10n_br_hr_contract.data.abstract"
    _description = "HR Data Base Abstract"
    _rec_names_search = ["code", "name"]

    code = fields.Char(required=True, index=True)

    name = fields.Char(required=True, index=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}"
