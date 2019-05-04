# Copyright (C) 2009 Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class Cnae(models.Model):
    _name = 'fiscal.cnae'
    _description = 'CNAE'

    code = fields.Char(
        string='Code',
        size=16,
        required=True)

    code_unmasked = fields.Char(
         string='Unmasked Code',
         size=10,
         compute='_compute_code_unmasked',
         store=True,
         index=True)

    name = fields.Text(
        string='Description',
        required=True)

    version = fields.Char(
        string='Version',
        size=16,
        required=True)

    parent_id = fields.Many2one(
        comodel_name='fiscal.cnae',
        string='Parent CNAE')

    child_ids = fields.One2many(
        comodel_name='fiscal.cnae',
        inverse_name='parent_id',
        string='Children CNAEs')

    internal_type = fields.Selection(
        selection=[('view', u'View'),
                   ('normal', 'Normal')],
        string='Internal Type',
        required=True,
        default='normal')

    _sql_constraints = [
        ('fiscal_cnae_code_uniq', 'unique (code)',
         'CNAE already exists with this code !')]

    @api.depends('code')
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = punctuation_rm(r.code)

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
