# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractSalaryUnit(models.Model):
    _name = "hr.contract.salary.unit"
    _description = "Unidade de pagamento da parte fixa da remuneração"

    name = fields.Char(string="Salary unit", required=True)

    code = fields.Char(string="Code", required=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record["name"]
            if name == "Monthly":
                name = "Por mês"
            elif name == "Biweekly":
                name = "Por 15 dias"
            elif name == "Weekly":
                name = "Por semana"
            elif name == "Daily":
                name = "Por dia"
            elif name == "Hourly":
                name = "Por hora"
            elif name == "Task":
                name = "Por tarefa"
            elif name == "Others":
                name = "Outros"

            name = record["code"] + " - " + name
            result.append((record["id"], name))
        return result
