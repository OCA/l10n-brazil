# Copyright (C) 2018  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from .constants.fiscal import FISCAL_IN_OUT_ALL, TAX_DOMAIN

class Cst(models.Model):
    _name = 'fiscal.cst'
    _inherit = 'fiscal.data.abstract'
    _order = 'tax_domain, code'
    _description = 'CST'

    code = fields.Char(
        size=4)

    type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        string='Type',
        required=True)

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        string='Tax Domain',
        required=True)

    _sql_constraints = [
        ('fiscal_cst_code_tax_domain_uniq', 'unique (code, tax_domain)',
         'CST already exists with this code !')]
