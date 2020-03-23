# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import FISCAL_IN_OUT, FISCAL_OUT, TAX_DOMAIN
from ..tools import misc


class TaxDefinition(models.Model):
    _name = 'l10n_br_fiscal.tax.definition'
    _description = 'Tax Definition'

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT,
        string='Type',
        required=True,
        default=FISCAL_OUT)

    tax_group_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.group',
        string='Tax Group')

    custom_tax = fields.Boolean(
        string='Custom Tax')

    tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax',
        domain="[('tax_group_id', '=', tax_group_id)]")

    cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST',
        domain="[('cst_type', 'in', (type_in_out, 'all')), "
               "('tax_domain', '=', tax_domain)]")

    cst_code = fields.Char(
        string='CST Code',
        related='cst_id.code')

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related='tax_group_id.tax_domain',
        store=True,
        string='Tax Domain')

    is_taxed = fields.Boolean(
        string='Taxed?')

    is_debit_credit = fields.Boolean(
        string='Debit/Credit?')

    tax_withholding = fields.Boolean(
        string='Tax Retention?')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')

    ncms = fields.Char(
        string='NCM List')

    ncm_exception = fields.Char(
        string='NCM Exeption')

    not_in_ncms = fields.Char(
        string='Not in NCM')

    ncm_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.ncm',
        relation='tax_definition_ncm_rel',
        colunm1='tax_definition_id',
        colunm2='ncm_id',
        compute='_compute_ncms',
        store=True,
        readonly=True,
        string='NCMs')

    cests = fields.Char(
        string='CEST')

    cest_ids = fields.Many2one(
        comodel_name='l10n_br_fiscal.cest',
        relation='tax_definition_cest_rel',
        colunm1='tax_definition_id',
        colunm2='ncm_id',
        compute='_compute_cests',
        store=True,
        readonly=True,
        string='CESTs')

    @api.multi
    @api.depends('ncms')
    def _compute_ncms(self):
        ncm = self.env['l10n_br_fiscal.ncm']
        for r in self:
            domain = []

            # Clear Field to recompute
            r.ncm_ids = False
            if r.ncms:
                domain = misc.domain_field_codes(r.ncms)

            if r.not_in_ncms:
                domain += misc.domain_field_codes(
                    field_codes=r.not_in_ncms,
                    operator1="!=", operator2="not ilike")

            if r.ncm_exception:
                domain += misc.domain_field_codes(
                    field_codes=r.ncm_exception,
                    field_name="exception",
                    code_size=2)

            if domain:
                r.ncm_ids = ncm.search(domain)

    @api.multi
    @api.depends('cests')
    def _compute_cests(self):
        cest = self.env['l10n_br_fiscal.cest']
        for r in self:
            domain = []

            # Clear Field
            r.cest_ids = False
            if r.cests:
                domain = misc.domain_field_codes(r.cests, code_size=7)

            if domain:
                r.cest_ids = cest.search(domain)

    @api.onchange('is_taxed')
    def _onchange_tribute(self):
        if not self.is_taxed:
            self.is_debit_credit = False
        else:
            self.is_debit_credit = True

    @api.onchange('custom_tax')
    def _onchange_custom_tax(self):
        if not self.custom_tax:
            self.tax_id = False
            self.cst_id = False

    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        if self.tax_id:
            if self.type_in_out == FISCAL_OUT:
                self.cst_id = self.tax_id.cst_out_id
            else:
                self.cst_id = self.tax_id.cst_in_id
