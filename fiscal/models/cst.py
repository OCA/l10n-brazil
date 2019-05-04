# Copyright (C) 2018  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from .constants.fiscal import FISCAL_IN_OUT, TAX_DOMAIN

class Cst(models.Model):
    _name = 'fiscal.cst'
    _order = 'tax_domain, code'
    _description = 'CST'

    code = fields.Char(
        string='Code',
        size=4,
        required=True)

    name = fields.Text(
        string='Name',
        required=True)

    type = fields.Selection(
        selection=[('in', 'In'),
                   ('out', 'Out'),
                   ('all', 'All')],
        string='Type',
        required=True)

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        string='Tax Domain',
        required=True)

    _sql_constraints = [
        ('fiscal_cst_code_tax_domain_uniq', 'unique (code, tax_domain)',
         'CST already exists with this code !')]

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name)
                      ('name', operator, name)]

        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        return [(r.id,
                 u"{0} - {1}".format(r.code, r.name))
                for r in self]
