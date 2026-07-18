# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractLaborRegime(models.Model):
    _name = "hr.contract.labor.regime"
    _inherit = "l10n_br_hr_contract.data.abstract"
    _description = "Type of employment contract"

    name = fields.Char(string="Labor regime")

    short_name = fields.Char()

    code = fields.Char(size=1)

    @api.depends("name", "short_name")
    def _compute_display_name(self):
        for record in self:
            if record.short_name:
                record.display_name = f"{record.short_name} - {record.name}"
            else:
                record.display_name = record.name
