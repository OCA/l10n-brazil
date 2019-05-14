# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from .constants.fiscal import FISCAL_IN_OUT, CFOP_DESTINATION

class Cfop(models.Model):
    _name = 'fiscal.cfop'
    _inherit = 'fiscal.data.abstract'
    _order = 'code'
    _description = 'CFOP'

    code = fields.Char(
        size=4,)

    small_name = fields.Char(
        string='Small Name',
        size=32,
        required=True)

    type = fields.Selection(
        selection=FISCAL_IN_OUT,
        string='Type',
        required=True)

    destination = fields.Selection(
        selection=CFOP_DESTINATION,
        string=u'Destination',
        required=True,
        help=u'Identifies the operation destination.')

    _sql_constraints = [
        ('fiscal_cfop_code_uniq', 'unique (code)',
         'CFOP already exists with this code !')]
