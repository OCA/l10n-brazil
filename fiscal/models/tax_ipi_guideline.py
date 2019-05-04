# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class TaxIpiGuideline(models.Model):
    _name = 'fiscal.tax.ipi.guideline'
    _description = 'IPI Guidelines'

    code = fields.Char(
        string='Code',
        size=3,
        required=True)

    name = fields.Text(
        string='Description',
        required=True)

    cst_group = fields.Selection(
        selection=[('imunidade', u'Imunidade'),
                   ('suspensao', u'Suspensão'),
                   ('isencao', u'Isenção'),
                   ('reducao', u'Redução'),
                   ('outros', u'Outros')],
        string='Group',
        required=True)

    cst_in_id = fields.Many2one(
        comodel_name='fiscal.cst',
        domain=[('domain', '=', 'ipi'),
                ('type', '=', 'in')],
        string=u'CST In')

    cst_out_id = fields.Many2one(
        comodel_name='fiscal.cst',
        domain=[('domain', '=', 'ipi'),
                ('type', '=', 'out')],
        string=u'CST Out')

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name + '%')
                      ('name', operator, name)]

        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        return [(r.id,
                 "{0} - {1}".format(r.code, r.name))
                for r in self]
