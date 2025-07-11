# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractLaborRegime(models.Model):
    _name = "hr.contract.labor.regime"
    _inherit = "l10n_br_hr_contract.data.abstract"
    _description = "Tipo de regime trabalhista"

    name = fields.Char(string="Labor regime")

    short_name = fields.Char(string="Short name")

    code = fields.Char(size=1)

    def name_get(self):
        data_names = []
        for data in self:
            name = data.name
            if data.short_name:
                name = f"{data.short_name} - {data.name}"
            data_names.append((data.id, name))
        return data_names
