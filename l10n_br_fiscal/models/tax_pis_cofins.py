# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _


class TaxPisCofins(models.Model):
    _name = 'l10n_br_fiscal.tax.pis.cofins'
    _description = 'Tax PIS/COFINS'

    code = fields.Char(
        string='Code',
        required=True)

    name = fields.Text(
        string='Name',
        required=True,
        index=True)

    piscofins_type = fields.Selection(
        selection=[
            ('ncm', _('NCM')),
            ('product', _('Product')),
            ('company', _('Company'))],
        default='ncm',
        string='Type',
        required=True,
        index=True)

    tax_pis_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax PIS',
        domain="[('tax_domain', '=', 'pis')]")

    tax_pis_st_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax PIS ST',
        domain="[('tax_domain', '=', 'pisst')]")

    tax_cofins_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax COFINS',
        domain="[('tax_domain', '=', 'cofins')]")

    tax_cofins_st_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax COFINS ST',
        domain="[('tax_domain', '=', 'cofinsst')]")

    ncms = fields.Char(
        string='NCM')

    ncm_exception = fields.Char(
        string='NCM Exeption')

    not_in_ncms = fields.Char(
        string='Not in NCM')

    ncm_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.ncm',
        relation='fiscal_pis_cofins_ncm_rel',
        colunm1='piscofins_id',
        colunm2='ncm_id',
        compute='_compute_ncms',
        store=True,
        readonly=True,
        string='NCMs')

    @api.depends('ncms')
    def _compute_ncms(self):
        ncm = self.env['l10n_br_fiscal.ncm']
        domain = False
        for r in self:
            # Clear Field
            domain = False
            r.ncm_ids = False
            if r.ncms:
                ncms = r.ncms.split(';')
                domain = ['|'] * (len(ncms) - 1)
                domain += [('code_unmasked', '=', n)
                           for n in ncms if len(n) == 8]
                domain += [('code_unmasked', '=ilike', n + '%')
                           for n in ncms if len(n) < 8]

            if r.not_in_ncms:
                not_in_ncms = r.not_in_ncms.split(';')
                domain += [('code_unmasked', '=', n)
                           for n in not_in_ncms if len(n) == 8]

                domain += [('code_unmasked', 'not ilike', n + '%')
                           for n in not_in_ncms if len(n) < 8]

            if r.ncm_exception:
                ncm_exception = r.ncm_exception.split(';')
                domain += [('exception', '=', n) for n in ncm_exception]

            if domain:
                r.ncm_ids = ncm.search(domain)
