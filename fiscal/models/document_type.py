# Copyright (C) 2009  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from .constants.fiscal import DOCUMENT_TYPE


class DocumentType(models.Model):
    _name = 'fiscal.document.type'
    _description = 'Fiscal Document Type'

    code = fields.Char(
        string='Code',
        size=8,
        required=True)

    name = fields.Char(
        string='Name',
        size=128,
        required=True)

    electronic = fields.Boolean(
        string='Is Eletronic')

    type = fields.Selection(
        selection=DOCUMENT_TYPE,
        string='Document Type',
        required=True)

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name + '%')
                      ('code_unmasked', operator, name),
                      ('name', operator, name)]

        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        return [(r.id,
                 "{0} - {1}".format(r.code, r.name))
                for r in self]
