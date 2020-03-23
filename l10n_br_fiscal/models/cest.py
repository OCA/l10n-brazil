# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import CEST_SEGMENT
from ..tools import misc


class Cest(models.Model):
    _name = 'l10n_br_fiscal.cest'
    _inherit = 'l10n_br_fiscal.data.product.abstract'
    _description = 'CEST'

    name = fields.Text(
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

    product_tmpl_ids = fields.One2many(
        inverse_name='cest_id')

    ncms = fields.Char(
        string='NCM')

    ncm_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.ncm',
        relation='fiscal_cest_ncm_rel',
        colunm1='cest_id',
        colunm2='ncm_id',
        compute='_compute_ncms',
        store=True,
        readonly=True,
        string='NCMs')

    @api.depends('ncms')
    def _compute_ncms(self):
        ncm = self.env['l10n_br_fiscal.ncm']
        for r in self:
            if r.ncms:
                domain = misc.domain_field_codes(r.ncms)
                r.ncm_ids = ncm.search(domain)
