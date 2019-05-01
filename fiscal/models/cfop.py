# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from .constants.fiscal import FISCAL_IN_OUT, CFOP_DESTINATION

class Cfop(models.Model):
    _name = 'fiscal.cfop'
    _order = 'code'
    _description = 'CFOP'

    code = fields.Char(
        string='Code',
        size=4,
        required=True)

    name = fields.Char(
        string='Name',
        size=256,
        required=True)

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
