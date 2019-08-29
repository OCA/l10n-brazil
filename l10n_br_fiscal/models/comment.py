# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from ..constants.fiscal import COMMENT_TYPE, COMMENT_TYPE_DEFAULT


class Comment(models.Model):
    _name = 'l10n_br_fiscal.comment'
    _description = 'Comment'
    _order = 'sequence'
    _rec_name = 'comment'

    sequence = fields.Integer(
        string='Sequence',
        default=10)

    name = fields.Char(
        string='Name',
        required=True)

    comment = fields.Text(
        string='Comment',
        required=True)

    comment_type = fields.Selection(
        selection=COMMENT_TYPE,
        string='Comment Type',
        default=COMMENT_TYPE_DEFAULT,
        required=True)

    object = fields.Selection(
        selection=[
            ('l10n_br_fiscal.document', 'Fiscal Document'),
            ('l10n_br_fiscal.document.line', 'Fiscal Document Line')],
        string='Object',
        required=True)

    date_begin = fields.Date(
        string='Initial Date')

    date_end = fields.Date(
        string='Final Date')

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name),
                      ('comment', 'ilike', '%' + name + '%')]
        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = '{0}...'.format(name[:60])
            return name

        return [(r.id, "{0}".format(truncate_name(r.name))) for r in self]
