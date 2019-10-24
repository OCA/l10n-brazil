# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrIdentityType(models.Model):
    _name = "hr.identity.type"
    _description = "Identity Types"

    name = fields.Char(string="Identity type", required=True)

    initials = fields.Char(string="Initials", required=True)

    employee_ids = fields.Many2many(string="Employees", comodel_name="hr.employee")
