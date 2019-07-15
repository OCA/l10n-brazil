# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..constants.fiscal import CEST_SEGMENT


class Cest(models.Model):
    _name = 'l10n_br_fiscal.cest'
    _inherit = 'l10n_br_fiscal.data.abstract'
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

    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        string='Products',
        compute='_compute_product_tmpl_info')

    product_tmpl_qty = fields.Integer(
        string='Products Quantity',
        compute='_compute_product_tmpl_info')

    @api.one
    def _compute_product_tmpl_info(self):
        product_tmpls = self.env['product.template'].search([
            ('cest_id', '=', self.id), '|',
            ('active', '=', False), ('active', '=', True)])
        self.product_tmpl_ids = product_tmpls
        self.product_tmpl_qty = len(product_tmpls)

    @api.depends('ncms')
    def _compute_ncms(self):
        ncm = self.env['l10n_br_fiscal.ncm']
        for r in self:
            if r.ncms:
                ncms = r.ncms.split(",")
                domain = ['|'] * (len(ncms) - 1)
                domain += [('code_unmasked', '=', n)
                           for n in ncms if len(n) == 8]
                domain += [('code_unmasked', '=ilike', n + '%')
                           for n in ncms if len(n) < 8]
                r.ncm_ids = ncm.search(domain)
