# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractLaborBondType(models.Model):
    _name = "hr.contract.labor.bond.type"
    _inherit = "l10n_br_hr_contract.data.abstract"
    _description = "Labor bond type"

    name = fields.Char(string="Labor bond type")
