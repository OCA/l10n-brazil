# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractSalaryUnit(models.Model):
    _name = "hr.contract.salary.unit"
    _description = "Unidade de pagamento da parte fixa da remuneração " \
                   "e-Social - S-2200 undSalFixo"

    name = fields.Char(
        string="Salary unit",
        required=True,
    )

    code = fields.Char(
        string="Code",
        required=True,
    )

    @api.multi
    def name_get(self):
        return [(record.id, "{} - {} ".format(record.code, record.name))
                for record in self]
