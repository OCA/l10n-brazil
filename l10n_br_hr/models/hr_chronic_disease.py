# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrChronicDisease(models.Model):
    _name = 'hr.chronic.disease'
    _description = 'Chronic Diseases'

    name = fields.Char(
        string='Disease name',
        required=True)

    employee_ids = fields.Many2many(
        string="Employee",
        comodel_name='hr.employee')
