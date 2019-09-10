# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
    TAX_FRAMEWORK_NORMAL,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_COFINS,
    PROFIT_CALCULATION,
    PROFIT_CALCULATION_PRESUMED,
    INDUSTRY_TYPE,
    INDUSTRY_TYPE_TRANSFORMATION
)


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
        default=TAX_FRAMEWORK_NORMAL,
        compute='_compute_l10n_br_data',
        inverse='_inverse_tax_framework',
        string='Tax Framework')

    profit_calculation = fields.Selection(
        selection=PROFIT_CALCULATION,
        default=PROFIT_CALCULATION_PRESUMED,
        string='Profit Calculation')

    is_industry = fields.Boolean(
        string='Is Industry',
        help='If your company is industry or ......',
        default=False)

    industry_type = fields.Selection(
        selection=INDUSTRY_TYPE,
        default=INDUSTRY_TYPE_TRANSFORMATION,
        string='Industry Type')

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

    piscofins_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.pis.cofins',
        string='PIS/COFINS',
        domain="[('piscofins_type', '=', 'company')]")

    ripi = fields.Boolean(
        string='RIPI')

    tax_ipi_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Default IPI',
        domain=[('tax_domain', '=', TAX_DOMAIN_IPI)])

    tax_icms_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Default ICMS',
        domain="[('tax_domain', 'in', ('icms', 'icmssn'))]")

    tax_issqn_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Default ISSQN',
        domain="[('tax_domain', '=', 'issqn')]")

    tax_definition_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.tax.definition.company',
        inverse_name='company_id',
        string='Tax Definition')

    def _del_tax_definition(self, tax_domain):
        tax_def = self.tax_definition_ids.filtered(
            lambda d: d.tax_group_id.tax_domain != tax_domain)
        self.tax_definition_ids = tax_def

    def _set_tax_definition(self, tax):
        tax_def = self.tax_definition_ids.filtered(
            lambda d: d.tax_group_id == tax.tax_group_id)

        tax_def_values = {
            'type_in_out': 'out',
            'tax_group_id': tax.tax_group_id.id,
            'is_taxed': True,
            'is_debit_credit': True,
            'custom_tax': True,
            'tax_id': tax.id,
            'cst_id': tax.cst_out_id.id,
            'tax_retention': False}

        if tax_def:
            tax_def.update(tax_def_values)
        else:
            self.tax_definition_ids = [(0, None, tax_def_values)]

    @api.onchange('cnae_main_id')
    def _onchange_cnae_main_id(self):
        if self.cnae_main_id:
            simplified_tax = self.env['l10n_br_fiscal.simplified.tax'].search(
                [('cnae_ids', '=', self.cnae_main_id.id)],
                limit=1)

            if simplified_tax:
                self.simplifed_tax_id = simplified_tax.id

    @api.onchange('profit_calculation', 'tax_framework')
    def _onchange_profit_calculation(self):

        # Get all Simples Nacional default taxes
        sn_piscofins_id = self.env.ref(
            'l10n_br_fiscal.tax_pis_cofins_simples_nacional')

        sn_tax_icms_id = self.env.ref(
            'l10n_br_fiscal.tax_icms_sn_com_credito')

        # If Tax Framework is Simples Nacional
        if self.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            # Set taxes
            self.piscofins_id = sn_piscofins_id
            self.tax_icms_id = sn_tax_icms_id

        # If Tax Framework is Regine Normal
        if self.tax_framework == TAX_FRAMEWORK_NORMAL:
            pis_cofins_refs = {
                'real': self.env.ref(
                    'l10n_br_fiscal.tax_pis_cofins_nao_columativo'),
                'presumed': self.env.ref(
                    'l10n_br_fiscal.tax_pis_cofins_columativo'),
                'arbitrary': self.env.ref(
                    'l10n_br_fiscal.tax_pis_cofins_columativo')}

            self.piscofins_id = pis_cofins_refs.get(self.profit_calculation)
            self.tax_icms_id = False

        self._onchange_cnae_main_id()
        self._onchange_piscofins_id()
        self._onchange_ripi()
        self._onchange_tax_ipi_id()
        self._onchange_tax_icms_id()
        self._onchange_tax_issqn_id()

    @api.onchange('is_industry')
    def _onchange_is_industry(self):
        if self.is_industry and self.tax_framework == TAX_FRAMEWORK_SIMPLES:
            self.ripi = True
        else:
            self.ripi = False

    @api.onchange('ripi')
    def _onchange_ripi(self):
        if not self.ripi and self.tax_framework == TAX_FRAMEWORK_NORMAL:
            self.tax_ipi_id = self.env.ref('l10n_br_fiscal.tax_ipi_nt')
        elif self.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            self.tax_ipi_id = self.env.ref(
                'l10n_br_fiscal.tax_ipi_simples_nacional')
            self.ripi = False
        else:
            self.tax_ipi_id = False

    @api.onchange('piscofins_id')
    def _onchange_piscofins_id(self):
        if self.piscofins_id:
            self._set_tax_definition(self.piscofins_id.tax_cofins_id)
            self._set_tax_definition(self.piscofins_id.tax_pis_id)
        else:
            self._del_tax_definition(TAX_DOMAIN_PIS)
            self._del_tax_definition(TAX_DOMAIN_COFINS)

    @api.onchange('tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        if self.tax_ipi_id:
            self._set_tax_definition(self.tax_ipi_id)
        else:
            self._del_tax_definition(TAX_DOMAIN_IPI)

    @api.onchange('tax_icms_id')
    def _onchange_tax_icms_id(self):
        if self.tax_icms_id:
            self._set_tax_definition(self.tax_icms_id)
        else:
            self._del_tax_definition(TAX_DOMAIN_ICMS)
            self._del_tax_definition(TAX_DOMAIN_ICMS_SN)

    @api.onchange('tax_issqn_id')
    def _onchange_tax_issqn_id(self):
        if self.tax_issqn_id:
            self._set_tax_definition(self.tax_issqn_id)
        else:
            self._del_tax_definition('issqn')
