# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractLaborBondType(models.Model):
    _name = "hr.contract.labor.bond.type"
    _description = "Labor bond type"

    name = fields.Char(string="Labor bond type", required=True)

    code = fields.Char(string="Code", required=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record["name"]
            if record["code"]:
                name = record["code"] + " - " + name
            result.append((record["id"], name))
        return result
