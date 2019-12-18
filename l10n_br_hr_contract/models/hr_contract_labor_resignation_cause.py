# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractResignationCause(models.Model):
    _name = "hr.contract.resignation.cause"
    _description = "Motivo da demissão"

    name = fields.Char(string="Resignation cause", required=True)

    code = fields.Char(string="Resignation cause code", required=True)

    fgts_withdraw_code = fields.Char(string="FGTS withdrawal code")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record["name"]
            if record["code"]:
                name = record["code"] + " - " + name
            result.append((record["id"], name))
        return result
