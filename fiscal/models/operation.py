# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .constants.fiscal import (
    FISCAL_IN_OUT
)


class Operation(models.Model):
    _name = 'fiscal.operation'
    _inherit = ['mail.thread']

    code = fields.Char(
        string='Code',
        required=True)

    name = fields.Char(
        string='Name',
        required=True)

    type = fields.Selection(
        selection=FISCAL_IN_OUT,
        string='Type',
        required=True)

    operation_line_ids = fields.One2many(
        comodel_name='fiscal.operation.line',
        inverse_name='operation_id',
        string='Operation Line')

    _sql_constraints = [
        ('fiscal_operation_code_uniq', 'unique (code)',
         'Fiscal Operation already exists with this code !')]
