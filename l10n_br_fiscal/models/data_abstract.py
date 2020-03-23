# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from odoo import api, fields, models
from odoo.osv import expression


class DataAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.data.abstract'
    _description = 'Fiscal Data Abstract'
    _order = 'code'

    code = fields.Char(
        string='Code',
        required=True,
        index=True)

    name = fields.Text(
        string='Name',
        required=True,
        index=True)

    code_unmasked = fields.Char(
        string='Unmasked Code',
        compute='_compute_code_unmasked',
        store=True,
        index=True)

    @api.depends('code')
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = misc.punctuation_rm(r.code)

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [
                '|',
                '|',
                ('code', operator, name),
                ('code_unmasked', 'ilike', name + '%'),
                ('name', operator, name),
            ]
        recs = self._search(expression.AND([domain, args]),
                            limit=limit,
                            access_rights_uid=name_get_uid)

        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = '{}...'.format(name[:60])
            return name

        if self._context.get('show_code_only'):
            return [(r.id, '{}'.format(r.code)) for r in self]

        return [(r.id, '{} - {}'.format(
            r.code, truncate_name(r.name))) for r in self]
