# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression

from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from .constants.fiscal import CEST_SEGMENT


class Cest(models.Model):
    _name = 'fiscal.cest'
    _order = 'code'
    _description = 'CEST'

    code = fields.Char(
        string='Code',
        required=True)

    code_unmasked = fields.Char(
         string='Unmasked Code',
         size=10,
         compute='_compute_code_unmasked',
         store=True,
         index=True)

    name = fields.Char(
        string='Name',
        required=True,
        index=True)

    item = fields.Char(
        string='Item',
        required=True,
        size=6)

    segment = fields.Selection(
        selection=CEST_SEGMENT,
        string='Segment',
        required=True)

    ncms = fields.Char(
        string='NCM')

    ncm_ids = fields.Many2many(
        comodel_name='fiscal.ncm',
        relation='fiscal_cest_ncm_rel',
        colunm1='cest_id',
        colunm2='ncm_id',
        compute='_compute_ncms',
        store=True,
        readonly=True,
        string='NCMs')

    @api.depends('code')
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = punctuation_rm(r.code)

    @api.depends('ncms')
    def _compute_ncms(self):
        ncm_ids = self.env['fiscal.ncm']
        for r in self:
            if r.ncms:
                ncms = r.ncms.split(",")
                domain = ['|'] * (len(ncms) - 1)
                domain += [('code_unmasked', '=', n)
                          for n in ncms if len(n) == 8]
                domain += [('code_unmasked', '=ilike', n + '%')
                           for n in ncms if len(n) < 8]
                ncm_ids = self.env['fiscal.ncm'].search(domain)
                r.ncm_ids = ncm_ids

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
                 u"{0} - {1}".format(r.code, r.name))
                for r in self]
