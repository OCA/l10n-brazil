# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .constants.fiscal import (
    FISCAL_IN_OUT_ALL,
    TAX_FRAMEWORK,
    CFOP_DESTINATION
)


class OperationLine(models.Model):
    _name = 'fiscal.operation.line'
    _description = 'Fiscal Operation Line'
    _inherit = ['mail.thread']

    operation_id = fields.Many2one(
        comodel_name='fiscal.operation',
        string='Operation',
        required=True,
        copy=False)

    cfop_id = fields.Many2one(
        comodel_name='fiscal.cfop',
        string='CFOP')

    cfop_destination = fields.Selection(
        selection=CFOP_DESTINATION,
        related="cfop_id.destination",
        string='CFOP destination')

    code = fields.Char(
        string='Code',
        required=True)

    type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        string='Type',
        required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'fiscal.operation.line'))

    line_inverse_id = fields.Many2one(
        comodel_name='fiscal.operation.line',
        string='Operation Line Inverse',
        domain="[('cfop_destination', '=', cfop_destination),('type', '!=', type)]",
        copy=False)

    line_refund_id = fields.Many2one(
        comodel_name='fiscal.operation.line',
        string='Operation Line Refund',
        domain="[('cfop_destination', '=', cfop_destination),"
               "('type', '!=', type)]",
        copy=False)

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Partner Tax Framework')

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Copmpany Tax Framework')

    _sql_constraints = [
        ('fiscal_operation_code_uniq', 'unique (code, operation_id)',
         'Fiscal Operation Line already exists with this code !')]
