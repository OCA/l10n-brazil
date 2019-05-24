# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ServiceType(models.Model):
    _name = 'fiscal.service.type'
    _inherit = 'fiscal.data.abstract'
    _description = 'Service Fiscal Type'

    parent_id = fields.Many2one(
        comodel_name='fiscal.service.type',
        string='Parent Service Type')

    child_ids = fields.One2many(
        comodel_name='fiscal.service.type',
        inverse_name='parent_id',
        string='Service Type Child')

    internal_type = fields.Selection(
        selection=[('view', 'View'),
                   ('normal', 'Normal')],
        string='Internal Type',
        required=True,
        default='normal')
