# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractResignationCause(models.Model):
    _name = "hr.contract.resignation.cause"
    _inherit = "l10n_br_hr_contract.data.abstract"
    _description = "Motivo da demissão"

    name = fields.Char(string="Resignation cause")

    code = fields.Char(string="Resignation cause code")

    fgts_withdraw_code = fields.Char(string="FGTS withdrawal code")
