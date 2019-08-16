# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import TAX_FRAMEWORK, TAX_FRAMEWORK_DEFAULT


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _compute_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """
        super(ResCompany, self)._compute_l10n_br_data()
        for c in self:
            c.tax_framework = c.partner_id.tax_framework
            c.cnae_main_id = c.partner_id.cnae_main_id

    def _inverse_cnae_main_id(self):
        """ Write the l10n_br specific functional fields. """
        for c in self:
            c.partner_id.cnae_main_id = c.cnae_main_id

    def _inverse_tax_framework(self):
        """ Write the l10n_br specific functional fields. """
        for c in self:
            c.partner_id.tax_framework = c.tax_framework

    @api.one
    @api.depends('simplifed_tax_id', 'annual_revenue')
    def _compute_simplifed_tax_range(self):
        tax_range = self.env['l10n_br_fiscal.simplified.tax.range'].search(
            [('inital_revenue', '<=', self.annual_revenue),
             ('final_revenue', '>=', self.annual_revenue)],
            limit=1)

        if tax_range:
            self.simplifed_tax_range_id = tax_range.id

    cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        compute='_compute_l10n_br_data',
        inverse='_inverse_cnae_main_id',
        domain="[('internal_type', '=', 'normal'), "
               "('id', 'not in', cnae_secondary_ids)]",
        string='Main CNAE')

    cnae_secondary_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.cnae',
        relation='res_company_fiscal_cnae_rel',
        colunm1='company_id',
        colunm2='cnae_id',
        domain="[('internal_type', '=', 'normal'), "
               "('id', '!=', cnae_main_id)]",
        string='Secondary CNAE')

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_DEFAULT,
        compute='_compute_l10n_br_data',
        inverse='_inverse_tax_framework',
        string='Tax Framework')

    annual_revenue = fields.Monetary(
        string='Annual Revenue',
        currency_field='currency_id',
        default=0.00,
        digits=dp.get_precision('Fiscal Documents'))

    simplifed_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.simplified.tax',
        domain="[('cnae_ids', '=', cnae_main_id)]",
        string='Simplified Tax')

    simplifed_tax_range_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.simplified.tax.range',
        domain="[('simplified_tax_id', '=', simplifed_tax_id)]",
        compute='_compute_simplifed_tax_range',
        store=True,
        readyonly=True,
        string='Simplified Tax Range')

    simplifed_tax_percent = fields.Float(
        string='Simplifed Tax Percent',
        default=0.00,
        related='simplifed_tax_range_id.total_tax_percent',
        digits=dp.get_precision('Fiscal Tax Percent'))

    ibpt_api = fields.Boolean(
        string='Use IBPT API',
        default=False)

    ibpt_token = fields.Char(
        string='IBPT Token')

    ibpt_update_days = fields.Integer(
        string='IBPT Token Updates',
        default=15)

    certificate_ecnpj_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.certificate',
        string='E-CNPJ',
        domain="[('type', '=', 'e-cnpj'), ('is_valid', '=', True)]")

    certificate_nfe_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.certificate',
        string='NFe',
        domain="[('type', '=', 'nf-e'), ('is_valid', '=', True)]")

    accountant_id = fields.Many2one(
        comodel_name='res.partner',
        string='Accountant')

    @api.onchange('cnae_main_id')
    def _onchange_cnae_main_id(self):
        simplified_tax = self.env['l10n_br_fiscal.simplified.tax'].search(
            [('cnae_ids', '=', self.cnae_main_id.id)],
            limit=1)

        if simplified_tax:
            self.simplifed_tax_id = simplified_tax.id
